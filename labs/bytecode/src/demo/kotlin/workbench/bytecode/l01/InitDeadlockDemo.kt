package workbench.bytecode.l01

import java.lang.management.ManagementFactory
import kotlin.concurrent.thread

// Two objects whose initializers need each other, started from two threads.
object KCast {
    @JvmField val ACTORS: Long
    init { pausePlease(); ACTORS = KCostumes.COUNT / 3 }   // needs KCostumes: 3 costumes an actor
}

object KCostumes {
    @JvmField val COUNT: Long
    init { pausePlease(); COUNT = KCast.ACTORS * 3 }       // needs KCast
}

private fun pausePlease() = Thread.sleep(200)

fun main(args: Array<String>) {
    // daemon threads, so the JVM can still exit at the end
    val a = thread(name = "cast", isDaemon = true) { println(KCast.ACTORS) }
    val b = thread(name = "costumes", isDaemon = true) { println(KCostumes.COUNT) }
    Thread.sleep(1_000)

    for (t in listOf(a, b)) {
        println("%-8s state=%s at %s".format(t.name, t.state, t.stackTrace[0]))
    }
    val stuck = ManagementFactory.getThreadMXBean().findDeadlockedThreads()
    println("deadlock detector: " + (stuck?.let { "${it.size} threads" } ?: "found nothing"))

    if (args.isNotEmpty()) {   // -Pargs=wait gives you 30 s to run jstack
        println("jstack ${ProcessHandle.current().pid()}   (search for 'Class initialization monitor')")
        Thread.sleep(30_000)
    }
}
