package workbench.concurrency.scratch

import java.time.Duration

class S05Buffer<T>(private val capacity: Int) {
    @Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
    private val lock = Object()                    // java.lang.Object, for wait() and notifyAll()
    private val items = ArrayDeque<T>()

    @Throws(InterruptedException::class)           // so Java callers see it, as in the Java version
    fun put(item: T) {
        synchronized(lock) {
            while (items.size == capacity) {       // 1. guard: re-check after every wake-up
                lock.wait()
            }
            items.addLast(item)                    // 2. act: condition holds, lock held
            lock.notifyAll()                       // 3. signal: the state changed
        }
    }

    @Throws(InterruptedException::class)
    fun take(): T {
        synchronized(lock) {
            while (items.isEmpty()) {
                lock.wait()
            }
            val head = items.removeFirst()
            lock.notifyAll()
            return head
        }
    }
}

class S05File {
    @Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
    private val lock = Object()
    private var fileArrived = false
    private var ready = false
    private val queue = java.util.ArrayDeque<String>()

    fun awaitFileOld(): Boolean {
        synchronized(lock) {
            if (!fileArrived) lock.wait(30_000)
            return fileArrived
        }
    }

    fun awaitFile(timeout: Duration): Boolean {
        val deadline = System.nanoTime() + timeout.toNanos()     // 1. fix the deadline once
        synchronized(lock) {
            while (!fileArrived) {                                // 2. guard on the condition
                val leftMillis = (deadline - System.nanoTime()) / 1_000_000
                if (leftMillis <= 0) return false                 // 3. out of time
                lock.wait(leftMillis)                             // 4. wait only for what's left
            }
            return true
        }
    }

    fun onFileArrived() {
        synchronized(lock) {
            fileArrived = true      // state first
            lock.notifyAll()        // then the signal
        }
    }

    fun guarded() {
        synchronized(lock) {          // lock is a java.lang.Object: Kotlin's Any has no wait()
            while (!ready) {
                lock.wait()           // give back the lock, sleep until woken, take the lock again
            }
            // here ready is true, and we hold the lock
        }
        synchronized(lock) {
            ready = true
            lock.notifyAll()          // wake every thread waiting on lock
        }
    }

    fun ifTake(): String {
        synchronized(lock) {
            if (queue.isEmpty()) lock.wait()   // checked once, before waiting
            return queue.removeFirst()         // NoSuchElementException
        }
    }
}
