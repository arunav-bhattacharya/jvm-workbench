package workbench.concurrency.scratch

import java.lang.management.ManagementFactory
import java.util.concurrent.ThreadLocalRandom
import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock

class S06Account(val id: Int) {
    private val l = ReentrantLock()
    fun lock() = l
    fun debit(c: Long) {}
    fun credit(c: Long) {}
}

fun transferBad(from: S06Account, to: S06Account, cents: Long) {
    synchronized(from) {
        synchronized(to) {
            from.debit(cents)
            to.credit(cents)
        }
    }
}

fun transferOrdered(from: S06Account, to: S06Account, cents: Long) {
    val first = if (from.id < to.id) from else to      // one order for everyone
    val second = if (first === from) to else from
    synchronized(first) {
        synchronized(second) {
            from.debit(cents)
            to.credit(cents)
        }
    }
}

fun tryOnce(from: S06Account, to: S06Account): Boolean {
    if (from.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
        try {
            if (to.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
                try { /* move the money */ return true }
                finally { to.lock().unlock() }
            }
        } finally {
            from.lock().unlock()       // couldn't get both: let go of everything
        }
    }
    Thread.sleep(ThreadLocalRandom.current().nextLong(1, 10))    // random back-off, then retry
    return false
}

fun health() {
    val ids: LongArray? = ManagementFactory.getThreadMXBean().findDeadlockedThreads()   // null if none
}

class Entry
class S06Ledger(private val auditLog: S06AuditLog) {
    private val entries = mutableListOf<Entry>()
    @Synchronized fun post(e: Entry) {
        entries += e
        auditLog.record(e)               // calls into AuditLog while holding the Ledger lock
    }
    @Synchronized fun balance(): Long = entries.size.toLong()
}

class S06AuditLog {
    lateinit var ledger: S06Ledger
    private val pending = mutableListOf<Entry>()
    @Synchronized fun record(e: Entry) { pending += e }
    @Synchronized fun flush() {
        val b = ledger.balance()         // calls into Ledger while holding the AuditLog lock
        write(pending, b)
        pending.clear()
    }
    private fun write(es: List<Entry>, b: Long) {}

    fun flushFixed() {
        val b = ledger.balance()             // 2. read the balance before taking our own lock
        val batch = synchronized(this) {
            pending.toList().also { pending.clear() }
        }
        write(batch, b)                      // 3. slow I/O with no lock at all
    }
}

class S06LedgerFixed(private val auditLog: S06AuditLog) {
    private val entries = mutableListOf<Entry>()
    fun post(e: Entry) {
        synchronized(this) { entries += e }
        auditLog.record(e)                   // 1. no Ledger lock held while calling out
    }
}

fun drill(from: S06Account, to: S06Account, cents: Long) {
    val first = if (from.id < to.id) from else to
    val second = if (first === from) to else from
    first.lock().lock()
    try {
        second.lock().lock()
        try {
            from.debit(cents)
            to.credit(cents)
        } finally {
            second.lock().unlock()
        }
    } finally {
        first.lock().unlock()
    }
}
