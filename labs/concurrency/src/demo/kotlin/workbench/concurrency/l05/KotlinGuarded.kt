package workbench.concurrency.l05

import java.util.ArrayDeque
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// Kotlin's Any has no wait()/notify(). The idiomatic guarded block uses a Lock and a Condition.
class KotlinBuffer<T>(private val capacity: Int) {
    private val lock = ReentrantLock()
    private val changed = lock.newCondition()      // one wait set, like a monitor's
    private val items = ArrayDeque<T>()

    fun put(item: T) = lock.withLock {
        while (items.size == capacity) changed.await()   // same while-loop guard
        items.addLast(item)
        changed.signalAll()                              // same as notifyAll()
    }

    fun take(): T = lock.withLock {
        while (items.isEmpty()) changed.await()
        items.removeFirst().also { changed.signalAll() }
    }
}

fun main() {
    val buffer = KotlinBuffer<Int>(2)
    val consumer = thread { repeat(5) { println("took ${buffer.take()}") } }
    repeat(5) { buffer.put(it) }
    consumer.join()
}
