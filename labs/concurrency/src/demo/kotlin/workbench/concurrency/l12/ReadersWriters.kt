package workbench.concurrency.l12

import java.util.concurrent.locks.ReentrantLock
import java.util.concurrent.locks.ReentrantReadWriteLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// Four readers keep a rate table busy for 1.5 s, overlapping all the time. One writer wants in once.
// How long does it wait with a hand-written readers-first lock, and with ReentrantReadWriteLock?
private interface RwLock { fun readLock(); fun readUnlock(); fun writeLock(); fun writeUnlock() }

// The textbook readers-first lock: a reader may enter whenever no writer is INSIDE.
private class ReadersFirst : RwLock {
    private val lock = ReentrantLock()
    private val changed = lock.newCondition()
    private var readers = 0
    private var writing = false
    override fun readLock() { lock.withLock { while (writing) changed.await(); readers++ } }
    override fun readUnlock() { lock.withLock { if (--readers == 0) changed.signalAll() } }
    override fun writeLock() { lock.withLock { while (writing || readers > 0) changed.await(); writing = true } }
    override fun writeUnlock() { lock.withLock { writing = false; changed.signalAll() } }
}

private class Jdk : RwLock {
    private val rw = ReentrantReadWriteLock()
    override fun readLock() = rw.readLock().lock()
    override fun readUnlock() = rw.readLock().unlock()
    override fun writeLock() = rw.writeLock().lock()
    override fun writeUnlock() = rw.writeLock().unlock()
}

private fun writerWaitMs(lock: RwLock): Long {
    val end = System.nanoTime() + 1_500_000_000L
    val readers = List(4) {
        thread {
            while (System.nanoTime() < end) {
                lock.readLock()
                try { Thread.sleep(2) } finally { lock.readUnlock() }   // a 2 ms read
            }
        }.also { Thread.sleep(1) }                            // stagger them so they overlap
    }
    Thread.sleep(100)
    val t0 = System.nanoTime()
    lock.writeLock()                                          // the refresh wants in
    val waited = (System.nanoTime() - t0) / 1_000_000
    lock.writeUnlock()
    readers.forEach { it.join() }
    return waited
}

fun main() {
    println("readers-first lock:     writer waited ${writerWaitMs(ReadersFirst())} ms")
    println("ReentrantReadWriteLock: writer waited ${writerWaitMs(Jdk())} ms")
}
