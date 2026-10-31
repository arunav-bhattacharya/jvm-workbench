package workbench.concurrency.l06

import java.lang.management.ManagementFactory

// Two transfers lock the same two accounts in opposite orders. Run with -Pargs=wait to keep it alive for jcmd.
private val accountA = Any()
private val accountB = Any()

fun main(args: Array<String>) {
    val stayAlive = args.firstOrNull() == "wait"
    val t1 = Thread({ move(accountA, accountB) }, "transfer-A-to-B").apply { isDaemon = true; start() }
    val t2 = Thread({ move(accountB, accountA) }, "transfer-B-to-A").apply { isDaemon = true; start() }
    Thread.sleep(1_000)

    val mx = ManagementFactory.getThreadMXBean()
    val ids = mx.findDeadlockedThreads()           // what a health check can ask the JVM
    println("deadlocked threads: ${ids?.size ?: 0}")
    ids?.let { mx.getThreadInfo(it) }?.forEach { info ->
        println("  ${info.threadName} is ${info.threadState}, wants a lock held by ${info.lockOwnerName}")
    }
    if (stayAlive) {
        val pid = ProcessHandle.current().pid()
        println("pid $pid: run  jcmd $pid Thread.print  in another terminal (60 s)")
        Thread.sleep(60_000)
    }
}

private fun move(from: Any, to: Any) {
    synchronized(from) {
        Thread.sleep(300)                          // widen the window: the other thread takes its first lock now
        synchronized(to) {
            println("${Thread.currentThread().name} moved the money")
        }
    }
}
