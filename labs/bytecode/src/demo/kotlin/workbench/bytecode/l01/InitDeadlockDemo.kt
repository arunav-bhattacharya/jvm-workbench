package workbench.bytecode.l01

import java.lang.management.ManagementFactory
import kotlin.concurrent.thread

// Two objects whose initializers need each other, started from two threads.
object KFxRates {
    @JvmField val EUR_USD: Long
    init { pausePlease(); EUR_USD = KFees.CARD_BPS + 108_000 }   // needs KFees
}

object KFees {
    @JvmField val CARD_BPS: Long
    init { pausePlease(); CARD_BPS = KFxRates.EUR_USD / 1_000 }  // needs KFxRates
}

private fun pausePlease() = Thread.sleep(200)

fun main(args: Array<String>) {
    // daemon threads, so the JVM can still exit at the end
    val a = thread(name = "rates", isDaemon = true) { println(KFxRates.EUR_USD) }
    val b = thread(name = "fees", isDaemon = true) { println(KFees.CARD_BPS) }
    Thread.sleep(1_000)

    for (t in listOf(a, b)) {
        println("%-5s state=%s at %s".format(t.name, t.state, t.stackTrace[0]))
    }
    val stuck = ManagementFactory.getThreadMXBean().findDeadlockedThreads()
    println("deadlock detector: " + (stuck?.let { "${it.size} threads" } ?: "found nothing"))

    if (args.isNotEmpty()) {   // -Pargs=wait gives you 30 s to run jstack
        println("jstack ${ProcessHandle.current().pid()}   (search for 'Class initialization monitor')")
        Thread.sleep(30_000)
    }
}
