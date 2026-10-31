package workbench.jmm.l01

import kotlin.concurrent.thread

private var stop = false   // plain field: no @Volatile, no lock

/** A worker spins until main sets a plain boolean. Does it ever notice? */
fun main() {
    // daemon, so the JVM can exit even if the worker never stops
    val worker = thread(isDaemon = true) {
        var spins = 0L
        while (!stop) {
            spins++
        }
        println("worker saw stop after %,d spins".format(spins))
    }

    Thread.sleep(1_000)   // give the JIT time to compile the loop
    stop = true
    println("main set stop = true")

    worker.join(3_000)
    println("worker still running 3 s later? ${worker.isAlive}")
}
