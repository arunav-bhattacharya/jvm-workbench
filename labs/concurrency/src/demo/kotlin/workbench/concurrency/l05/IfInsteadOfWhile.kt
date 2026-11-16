package workbench.concurrency.l05

import java.util.ArrayDeque

// Two cooks wait on an empty rail. One order arrives. The guard is an `if`.
@Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
private val lock = Object()
private val rail = ArrayDeque<String>()

private fun take(): String {
    synchronized(lock) {
        if (rail.isEmpty()) {                  // BUG: checked once, never again after waking
            lock.wait()
        }
        return rail.removeFirst()              // throws NoSuchElementException if someone else took it
    }
}

fun main() {
    val cook = Runnable {
        try {
            println("${Thread.currentThread().name} took ${take()}")
        } catch (e: Exception) {
            println("${Thread.currentThread().name} failed: $e")
        }
    }
    val c1 = Thread(cook, "cook-1")
    val c2 = Thread(cook, "cook-2")
    c1.start()
    c2.start()
    while (c1.state != Thread.State.WAITING || c2.state != Thread.State.WAITING) {
        Thread.sleep(10)                       // wait until both are parked in wait()
    }
    synchronized(lock) {
        rail.addLast("order-1")                // one order...
        lock.notifyAll()                       // ...and both cooks wake up
    }
    c1.join(2_000)
    c2.join(2_000)
    if (c1.isAlive || c2.isAlive) {            // with `while`, one cook goes back to waiting
        println("one cook is still waiting; giving it a second order")
        synchronized(lock) {
            rail.addLast("order-2")
            lock.notifyAll()
        }
    }
    c1.join()
    c2.join()
}
