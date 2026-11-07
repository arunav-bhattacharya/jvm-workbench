package workbench.concurrency.l07

import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantReadWriteLock
import kotlin.concurrent.read
import kotlin.concurrent.write

// One thread, one ReentrantReadWriteLock. Upgrading (read, then write) never succeeds.
// Downgrading (write, then read, then release the write) is allowed.
// Run with -Pargs=hang to use lock() instead of tryLock() and see the thread wait forever.
fun main(args: Array<String>) {
    val rw = ReentrantReadWriteLock()
    val hang = args.firstOrNull() == "hang"

    // 1. the "upgrade": ask for the write lock while still holding the read lock
    rw.readLock().lock()
    try {
        println("holding the read lock, read holds = ${rw.readHoldCount}")
        if (hang) {
            println("calling writeLock().lock() ... (pid ${ProcessHandle.current().pid()}, Ctrl+C to stop)")
            rw.writeLock().lock()                                    // waits for every reader to leave, us included
        }
        val got = rw.writeLock().tryLock(1, TimeUnit.SECONDS)        // the same wait, with a time limit
        println("write lock while holding a read lock, after 1 s: $got")
    } finally {
        rw.readLock().unlock()
    }

    // 2. the downgrade: write lock, then read lock, then let go of the write lock
    rw.writeLock().lock()
    try {
        rw.readLock().lock()                                         // allowed: we are the only writer
    } finally {
        rw.writeLock().unlock()
    }
    try {
        println("downgraded: write locked = ${rw.isWriteLocked}, read holds = ${rw.readHoldCount}")
    } finally {
        rw.readLock().unlock()
    }

    // 3. Kotlin only: write {} inside read {} does not hang, because write {} first lets go of
    //    this thread's read locks. That makes it a release-then-acquire, not an atomic upgrade.
    rw.read {
        rw.write { println("kotlin write {} inside read {}: write locked = ${rw.isWriteLocked}, read holds = ${rw.readHoldCount}") }
    }
}
