package workbench.ledger.l03

import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

/**
 * Caps how many calls are inside one slow dependency at once. Create one per dependency and share
 * it with every request: a bulkhead created per request limits nothing.
 */
class Bulkhead(val permits: Int) {
    private val inFlight = Semaphore(permits)

    /**
     * Runs [block] while holding one permit, and returns its result.
     *
     * TODO:
     * 1. `tryAcquire` one permit, waiting at most [waitNanos] (`TimeUnit.NANOSECONDS`). If none
     *    comes in time, throw [TimeoutException] without running [block].
     * 2. Acquire before the `try`: a thread that never got a permit must never release one.
     * 3. Run [block] inside `try` and `release()` in `finally`, so the permit comes back even when
     *    [block] throws or is interrupted.
     */
    fun <T> call(waitNanos: Long, block: () -> T): T {
        TODO("tryAcquire with the wait, run the block, release in finally")
    }

    /** Permits free right now. */
    fun available(): Int = inFlight.availablePermits()
}
