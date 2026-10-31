package workbench.concurrency.scratch

import java.math.BigDecimal

class S04Transfer {
    private var a = 0L
    private var b = 0L
    private val lock = Any()

    fun transfer(cents: Long) {
        synchronized(lock) {      // take lock's monitor, or wait until it is free
            a -= cents
            b += cents
        }                         // release it
    }
}

class S04Account {
    private var balanceCents = 0L
    @Synchronized fun withdraw(cents: Long) {
        if (canCover(cents)) balanceCents -= cents   // canCover is synchronized too
    }

    @Synchronized fun canCover(cents: Long): Boolean = balanceCents >= cents
}

fun interface Listener { fun onRate(pair: String, rate: BigDecimal) }

class S04Board {
    private val lock = Any()
    private val rates = HashMap<String, BigDecimal>()
    private val listeners = ArrayList<Listener>()
    fun publish(pair: String, rate: BigDecimal) {
        val toNotify = synchronized(lock) {
            rates[pair] = rate                   // 1. our state, under the lock
            listeners.toList()                   // 2. a snapshot to work from (the block's value)
        }
        for (l in toNotify) l.onRate(pair, rate) // 3. alien code, no lock held
    }
}

object riskTeam { fun notifyLargeRefund(c: Long) {} }

class RefundLimiterOld {
    companion object {
        private var refundedCents = 0L                    // shared by every instance
        private const val LIMIT_CENTS = 5_000_000L
    }

    @Synchronized fun tryRefund(cents: Long): Boolean {   // locks `this`
        if (refundedCents + cents > LIMIT_CENTS) return false
        riskTeam.notifyLargeRefund(cents)                 // HTTP call, about 300 ms
        refundedCents += cents
        return true
    }
}

class RefundLimiterNew {
    companion object {
        private val LOCK = Any()                          // 1. one lock for the shared state
        private var refundedCents = 0L
        private const val LIMIT_CENTS = 5_000_000L
    }

    fun tryRefund(cents: Long): Boolean {
        synchronized(LOCK) {                              // 2. check and reserve as one step
            if (refundedCents + cents > LIMIT_CENTS) return false
            refundedCents += cents
        }
        try {
            riskTeam.notifyLargeRefund(cents)             // 3. slow call, no lock held
            return true
        } catch (e: RuntimeException) {
            synchronized(LOCK) { refundedCents -= cents } // 4. undo the reservation
            throw e
        }
    }
}

class StatusBoard {
    private val lock = Any()
    private val listeners = mutableListOf<(String) -> Unit>()
    private var status: String? = null

    fun subscribe(l: (String) -> Unit) {
        synchronized(lock) { listeners += l }
    }

    fun update(newStatus: String) {
        val toNotify = synchronized(lock) {
            status = newStatus
            listeners.toList()
        }
        for (l in toNotify) l(newStatus)
    }
}
