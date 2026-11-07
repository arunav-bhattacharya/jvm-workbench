package workbench.performance.l05

import jdk.jfr.Category
import jdk.jfr.Description
import jdk.jfr.Event
import jdk.jfr.Label
import jdk.jfr.Name
import java.math.BigDecimal
import java.math.RoundingMode
import java.nio.file.Path
import java.util.concurrent.ThreadLocalRandom
import kotlin.concurrent.thread

// Kotlin twin of JfrDemo.java (with its workload and event in this one file). It runs the workload
// for 4 seconds in a second JVM started with -XX:StartFlightRecording and writes build/perf05-kt.jfr.

@Name("workbench.IssuerCall")
@Label("Issuer Call")
@Category("Workbench", "Payments")
@Description("A call to the card issuer during authorization")
class KIssuerCallEvent : Event() {
    @Label("Merchant") var merchant: String? = null        // a Kotlin property: JFR records its field
    @Label("Amount (cents)") var amountCents = 0L
    @Label("Approved") var approved = false
}

private val ledger = Any()

fun kFee(amount: String): Long =
    (BigDecimal(amount) * BigDecimal("0.029")).setScale(2, RoundingMode.HALF_EVEN).unscaledValue().toLong()

fun kCallIssuer(merchant: String, cents: Long): Boolean {
    val event = KIssuerCallEvent()
    event.begin()
    Thread.sleep(ThreadLocalRandom.current().nextInt(2, if (merchant == "m_7") 40 else 12).toLong())
    val approved = cents < 400_000
    event.end()
    if (event.shouldCommit()) {                            // skip the field work when no recording wants it
        event.merchant = merchant
        event.amountCents = cents
        event.approved = approved
        event.commit()
    }
    return approved
}

fun kRunWorkload(seconds: Int) {
    val until = System.nanoTime() + seconds * 1_000_000_000L
    val workers = (0 until 4).map { w ->
        thread(name = "auth-$w") {
            var sink = 0L
            var i = 0
            while (System.nanoTime() < until) {
                for (k in 0 until 2_000) sink += kFee("${100 + (k + i) % 9_000}.25")
                kCallIssuer("m_${i % 10}", 1_000 + (i * 7_919L) % 500_000)
                if (i % 25 == w) synchronized(ledger) { Thread.sleep(15) }   // a ledger write under a shared lock
                i++
            }
            if (sink == 42L) println()
        }
    }
    workers.forEach { it.join() }
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") return kRunWorkload(4)
    val file = Path.of("build", "perf05-kt.jfr").toAbsolutePath()
    val java = ProcessHandle.current().info().command().orElse("java")
    ProcessBuilder(java, "-XX:StartFlightRecording:filename=$file,settings=profile",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l05.JfrDemoKt", "child")
        .inheritIO().start().waitFor()
    println("recording written to $file")
    println("try: jfr summary $file")
}
