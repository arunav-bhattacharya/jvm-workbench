package workbench.concurrency.l02

import kotlin.concurrent.thread

// Puts threads into each of the six states and prints what getState() reports.
@Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
private val monitor = Object()                    // java.lang.Object, because Kotlin's Any has no wait()

@Volatile private var spin = true

fun main() {
    val sleeper = Thread({ pause(2_000) }, "sleeper")
    println("%-24s%s".format("before start():", sleeper.state))
    sleeper.start()
    show(sleeper, Thread.State.TIMED_WAITING, "inside sleep(2000):")

    val busy = thread(name = "busy") { while (spin) Thread.onSpinWait() }
    show(busy, Thread.State.RUNNABLE, "in a busy loop:")

    val waiter = thread(name = "waiter") {
        synchronized(monitor) {
            try {
                monitor.wait()                     // no timeout
            } catch (e: InterruptedException) {
                println("waiter interrupted, flag now ${Thread.currentThread().isInterrupted}")
            }
        }
    }
    show(waiter, Thread.State.WAITING, "inside wait():")

    val blocked = Thread({ synchronized(monitor) { } }, "blocked")
    synchronized(monitor) {                        // main holds the monitor...
        blocked.start()                            // ...so this thread cannot enter
        show(blocked, Thread.State.BLOCKED, "entering a held lock:")
    }

    spin = false
    val all = listOf(sleeper, busy, waiter, blocked)
    all.forEach { it.interrupt() }
    all.forEach { it.join() }
    println("%-24s%s".format("after join():", sleeper.state))
}

// getState() is a snapshot, so poll until the thread gets where we sent it
private fun show(t: Thread, expected: Thread.State, label: String) {
    var i = 0
    while (i++ < 200 && t.state != expected) Thread.sleep(10)
    println("%-24s%s".format(label, t.state))
}

private fun pause(ms: Long) {
    try {
        Thread.sleep(ms)
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()
    }
}
