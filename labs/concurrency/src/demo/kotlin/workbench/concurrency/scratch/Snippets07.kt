package workbench.concurrency.scratch

import java.math.BigDecimal
import java.time.Duration
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock
import java.util.concurrent.locks.ReentrantReadWriteLock
import java.util.concurrent.locks.StampedLock
import kotlin.concurrent.read
import kotlin.concurrent.withLock
import kotlin.concurrent.write

class S07Entry
class S07Ledger {
    private val lock = ReentrantLock()
    private val entries = mutableListOf<S07Entry>()       // guarded by lock

    fun post(e: S07Entry) {
        lock.withLock {            // kotlin.concurrent: lock(), try, finally unlock()
            entries += e
        }
    }
}

class S07Buffer<T>(private val capacity: Int) {
    private val items = ArrayDeque<T>()
    private val lock = ReentrantLock()
    private val notFull = lock.newCondition()      // producers wait here
    private val notEmpty = lock.newCondition()     // consumers wait here

    fun put(item: T) = lock.withLock {
        while (items.size == capacity) notFull.await()   // releases the lock while waiting
        items.addLast(item)
        notEmpty.signal()                                 // wake one consumer
    }

    fun take(): T = lock.withLock {
        while (items.isEmpty()) notEmpty.await()
        val head = items.removeFirst()
        notFull.signal()                                  // wake one producer
        head
    }
}

class S07Rates(private val loader: (String) -> BigDecimal) {
    private val rw = ReentrantReadWriteLock()
    private val rates = HashMap<String, BigDecimal>()    // guarded by rw

    fun rate(pair: String): BigDecimal? = rw.read {     // many threads can hold this at once
        rates[pair]
    }

    fun refresh(fresh: Map<String, BigDecimal>) = rw.write {   // waits until no reader and no writer holds the lock
        rates.clear()
        rates.putAll(fresh)
    }

    fun rateOrLoadBroken(pair: String): BigDecimal {
        rw.readLock().lock()
        try {
            val r = rates[pair]
            if (r != null) return r
            rw.writeLock().lock()         // waits for every reader to leave, this thread included: forever
            try {
                return loader(pair).also { rates[pair] = it }
            } finally {
                rw.writeLock().unlock()
            }
        } finally {
            rw.readLock().unlock()
        }
    }

    fun rateOrLoad(pair: String): BigDecimal {
        rw.read { rates[pair]?.let { return it } }       // 1. fast path under the read lock
        return rw.write {                                // 2. read lock released, write lock taken
            rates.getOrPut(pair) { loader(pair) }        // 3. re-check: someone may have loaded it
        }
    }

    // compare block
    fun rateCompare(pair: String): BigDecimal = rw.read {
        rates[pair] ?: rw.write {
            // write {} let go of our read lock first, so another thread may have loaded it: re-check
            rates.getOrPut(pair) { loader(pair) }
        }
    }
}

data class S07Quote(val bid: Long, val ask: Long)
class S07Board {
    private val lock = StampedLock()
    private var bid = 100L
    private var ask = 102L

    fun quote(): S07Quote {
        var stamp = lock.tryOptimisticRead()     // 1. no lock, just a version number
        var b = bid; var a = ask                 // 2. copy into locals
        if (!lock.validate(stamp)) {             // 3. a writer got in: the copies may be torn
            stamp = lock.readLock()              // 4. fall back to a real read lock
            try { b = bid; a = ask } finally { lock.unlockRead(stamp) }
        }
        return S07Quote(b, a)                    // 5. use the locals only after validate
    }
}

class CardBusyException(cardId: String) : RuntimeException("card $cardId is busy")

class S07CardLocks {
    private val locks = ConcurrentHashMap<String, ReentrantLock>()

    fun <T> withCard(cardId: String, maxWait: Duration, action: () -> T): T {
        // 1. one lock per card, created at most once
        val lock = locks.computeIfAbsent(cardId) { ReentrantLock() }
        // 2. wait a bounded time; an interrupt also ends the wait
        if (!lock.tryLock(maxWait.toNanos(), TimeUnit.NANOSECONDS)) {
            throw CardBusyException(cardId)               // 3. busy: fail fast, the client retries
        }
        try {
            return action()                               // 4. critical section
        } finally {
            lock.unlock()                                 // 5. always release
        }
    }

    private val stripes = Array(256) { ReentrantLock() }

    fun lockFor(cardId: String): ReentrantLock =
        stripes[Math.floorMod(cardId.hashCode(), stripes.size)]          // two cards may share a stripe: fine
}
