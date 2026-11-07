package workbench.ledger.l03

import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

class Bulkhead(val permits: Int) {
    private val inFlight = Semaphore(permits)

    fun <T> call(waitNanos: Long, block: () -> T): T {
        // 1. wait no longer than the request can afford; outside the try, so a failed wait releases nothing
        if (!inFlight.tryAcquire(waitNanos, TimeUnit.NANOSECONDS)) {
            throw TimeoutException("no permit within ${waitNanos / 1_000_000} ms")
        }
        try {
            return block()                  // 2. only the slow call holds the permit
        } finally {
            inFlight.release()              // 3. always given back: on success, on failure, on interrupt
        }
    }

    fun available(): Int = inFlight.availablePermits()
}
