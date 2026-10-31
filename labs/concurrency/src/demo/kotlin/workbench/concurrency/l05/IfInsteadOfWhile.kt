package workbench.concurrency.l05

import java.util.ArrayDeque

// Two consumers wait on an empty queue. One item arrives. The guard is an `if`.
@Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
private val lock = Object()
private val queue = ArrayDeque<String>()

private fun take(): String {
    synchronized(lock) {
        if (queue.isEmpty()) {                 // BUG: checked once, never again after waking
            lock.wait()
        }
        return queue.removeFirst()             // throws NoSuchElementException if someone else took it
    }
}

fun main() {
    val consumer = Runnable {
        try {
            println("${Thread.currentThread().name} took ${take()}")
        } catch (e: Exception) {
            println("${Thread.currentThread().name} failed: $e")
        }
    }
    val c1 = Thread(consumer, "consumer-1")
    val c2 = Thread(consumer, "consumer-2")
    c1.start()
    c2.start()
    while (c1.state != Thread.State.WAITING || c2.state != Thread.State.WAITING) {
        Thread.sleep(10)                       // wait until both are parked in wait()
    }
    synchronized(lock) {
        queue.addLast("auth-1")                // one item...
        lock.notifyAll()                       // ...and both consumers wake up
    }
    c1.join(2_000)
    c2.join(2_000)
    if (c1.isAlive || c2.isAlive) {            // with `while`, one consumer goes back to waiting
        println("one consumer is still waiting; giving it a second item")
        synchronized(lock) {
            queue.addLast("auth-2")
            lock.notifyAll()
        }
    }
    c1.join()
    c2.join()
}
