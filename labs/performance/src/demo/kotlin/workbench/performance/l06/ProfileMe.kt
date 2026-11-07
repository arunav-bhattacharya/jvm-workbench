package workbench.performance.l06

import java.math.BigDecimal
import java.math.RoundingMode
import kotlin.concurrent.thread

// Kotlin twin of ProfileMe.java (with SlowFees in Kotlin): four threads run kFeeSlow for 8 seconds.
// While it runs, attach from another terminal:  asprof -d 5 -f cpu.html <pid>

data class KPayment(val id: String, val currency: String, val amount: String, val merchant: String)

@Volatile var kDebugEnabled = false                     // DEBUG logging is off in production

fun kDebug(message: String) { if (kDebugEnabled) println(message) }

fun kFeeSlow(p: KPayment): Long {
    require(Regex("^[A-Z]{3}$").matches(p.currency)) { "bad currency" }   // a regex compiled per call
    val amount = BigDecimal(p.amount)
    val fee = (amount * BigDecimal("0.029") + BigDecimal("0.30")).setScale(2, RoundingMode.HALF_EVEN)
    kDebug("payment %s merchant=%s amount=%s fee=%s"                       // formatted, then thrown away
        .format(p.id, p.merchant, amount.toPlainString(), fee.toPlainString()))
    return fee.unscaledValue().toLong()
}

fun kPayments(n: Int) = Array(n) { i ->
    KPayment("pay_$i", if (i % 2 == 0) "EUR" else "USD", "${1 + (i * 7_919) % 99_999}.${10 + i % 89}", "m_${i % 50}")
}

fun kHammer(threads: Int, untilNanos: Long) {
    val ps = kPayments(4_096)
    (0 until threads).map { seed ->
        thread(name = "fees-$seed") {
            var sink = 0L
            var i = seed
            while (System.nanoTime() < untilNanos) sink += kFeeSlow(ps[i++ and 4095])
            if (sink == 42L) println()
        }
    }.forEach { it.join() }
}

fun main(args: Array<String>) {
    val seconds = args.firstOrNull()?.toInt() ?: 8
    val pid = ProcessHandle.current().pid()
    println("pid $pid, running for $seconds s")
    println("attach with: asprof -d 5 -f cpu.html $pid")
    kHammer(4, System.nanoTime() + seconds * 1_000_000_000L)
    println("done")
}
