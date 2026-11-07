package workbench.performance.l07

import jdk.jfr.Configuration
import jdk.jfr.Recording
import jdk.jfr.consumer.RecordingFile
import java.lang.management.ManagementFactory
import java.math.BigDecimal
import java.math.RoundingMode
import java.nio.file.Path
import kotlin.concurrent.thread

// Kotlin twin of FeeInvestigation.java: the same three fee versions written in Kotlin, run on 4 threads
// for 3 seconds with an in-process JFR recording, then allocation by line in this file.
// Usage: -Pargs=slow (or hoisted, noregex).

data class KtPayment(val id: String, val currency: String, val amount: String, val merchant: String)

@Volatile var ktDebugEnabled = false
fun ktDebug(message: String) { if (ktDebugEnabled) println(message) }

// before: a regex per call, constants per call, a log line formatted and dropped
fun ktFeeSlow(p: KtPayment): Long {
    require(Regex("^[A-Z]{3}$").matches(p.currency)) { "bad currency" }
    val amount = BigDecimal(p.amount)
    val fee = (amount * BigDecimal("0.029") + BigDecimal("0.30")).setScale(2, RoundingMode.HALF_EVEN)
    ktDebug("payment %s merchant=%s amount=%s fee=%s".format(p.id, p.merchant, amount.toPlainString(), fee.toPlainString()))
    return fee.unscaledValue().toLong()
}

// round 1: hoisted constants and pattern, guarded log line
val KT_CCY = Regex("^[A-Z]{3}$")
val KT_RATE = BigDecimal("0.029")
val KT_FIXED = BigDecimal("0.30")

fun ktFeeHoisted(p: KtPayment): Long {
    require(KT_CCY.matches(p.currency)) { "bad currency" }
    val amount = BigDecimal(p.amount)
    val fee = (amount * KT_RATE + KT_FIXED).setScale(2, RoundingMode.HALF_EVEN)
    if (ktDebugEnabled) ktDebug("payment %s merchant=%s amount=%s fee=%s".format(p.id, p.merchant, amount.toPlainString(), fee.toPlainString()))
    return fee.unscaledValue().toLong()
}

// round 2: no regex for three letters
fun isCurrencyCodeKt(s: String) = s.length == 3 && s.all { it in 'A'..'Z' }

fun ktFeeNoRegex(p: KtPayment): Long {
    require(isCurrencyCodeKt(p.currency)) { "bad currency" }
    val amount = BigDecimal(p.amount)
    val fee = (amount * KT_RATE + KT_FIXED).setScale(2, RoundingMode.HALF_EVEN)
    if (ktDebugEnabled) ktDebug("payment %s merchant=%s amount=%s fee=%s".format(p.id, p.merchant, amount.toPlainString(), fee.toPlainString()))
    return fee.unscaledValue().toLong()
}

fun ktPayments(n: Int) = Array(n) { i ->
    KtPayment("pay_$i", if (i % 2 == 0) "EUR" else "USD", "${1 + (i * 7_919) % 99_999}.${10 + i % 89}", "m_${i % 50}")
}

fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "slow"
    val fee: (KtPayment) -> Long = when (mode) { "slow" -> ::ktFeeSlow; "hoisted" -> ::ktFeeHoisted; else -> ::ktFeeNoRegex }
    val ps = ktPayments(4_096)
    val file = Path.of("build", "fees-kt-$mode.jfr").toAbsolutePath()
    val calls = LongArray(4)
    Recording(Configuration.getConfiguration("profile")).use { rec ->
        rec.start()
        val end = System.nanoTime() + 3_000_000_000L
        (0 until 4).map { t ->
            thread {
                var sink = 0L
                var i = t
                while (System.nanoTime() < end) { sink += fee(ps[i and 4095]); i++; calls[t]++ }
                if (sink == 42L) println()
            }
        }.forEach { it.join() }
        rec.stop()
        rec.dump(file)
    }
    val gcs = ManagementFactory.getGarbageCollectorMXBeans().sumOf { it.collectionCount }
    println("%s: %,d calls/s, %d GCs".format(mode, calls.sum() / 3, gcs))

    val weight = HashMap<String, Long>()
    for (e in RecordingFile.readAllEvents(file)) {
        if (e.eventType.name != "jdk.ObjectAllocationSample") continue
        val frame = e.stackTrace?.frames?.firstOrNull { it.method.type.name == "workbench.performance.l07.FeeInvestigationKt" } ?: continue
        weight.merge("${frame.method.name} line ${frame.lineNumber}", e.getLong("weight"), Long::plus)
    }
    val total = weight.values.sum()
    println("allocation by line in FeeInvestigation.kt:")
    weight.entries.sortedByDescending { it.value }.take(5)
        .forEach { (site, w) -> println("  %5.1f%%  %s".format(100.0 * w / total, site)) }
}
