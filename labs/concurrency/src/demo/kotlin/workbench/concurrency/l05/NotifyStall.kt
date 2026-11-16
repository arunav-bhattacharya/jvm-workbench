package workbench.concurrency.l05

import java.util.ArrayDeque
import java.util.concurrent.atomic.AtomicLong

// A rail with room for one order, shared by 2 waiters and 2 cooks. Uses notify(), or notifyAll() with -Pargs=all.
@Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
private val lock = Object()
private val slot = ArrayDeque<Int>()
private val moved = AtomicLong()
private var all = false                        // set once in main, before the threads start

private fun put(x: Int) {
    synchronized(lock) {
        while (!slot.isEmpty()) lock.wait()
        slot.addLast(x)
        signal()                               // notify() wakes ONE waiting thread: maybe a cook, maybe the other waiter
    }
}

private fun take(): Int {
    synchronized(lock) {
        while (slot.isEmpty()) lock.wait()
        val x = slot.removeFirst()
        signal()
        return x
    }
}

private fun signal() {
    if (all) lock.notifyAll() else lock.notify()
}

fun main(args: Array<String>) {
    all = args.firstOrNull() == "all"
    println(if (all) "using notifyAll()" else "using notify()")
    val threads = List(4) { i ->
        val producer = i < 2
        Thread({
            try {
                while (true) {
                    if (producer) put(1) else { take(); moved.incrementAndGet() }
                }
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            }
        }, (if (producer) "waiter-" else "cook-") + (i % 2)).apply {
            isDaemon = true
            start()
        }
    }
    var last = -1L
    for (second in 1..5) {
        Thread.sleep(1_000)
        val now = moved.get()
        if (now == last) {
            println("stalled after %,d orders. Thread states:".format(now))
            threads.forEach { println("  ${it.name}: ${it.state}") }
            return
        }
        println("after %d s: %,d orders cooked".format(second, now))
        last = now
    }
    println(if (all) "no stall: notifyAll() wakes every waiting thread, so the right kind always gets a turn"
            else "no stall this time; it depends on timing, so run it again")
}
