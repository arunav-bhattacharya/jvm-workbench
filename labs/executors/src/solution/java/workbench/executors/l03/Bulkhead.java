package workbench.executors.l03;

import java.time.Duration;
import java.util.concurrent.Callable;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;

public final class Bulkhead {
    private final String name;
    private final Duration maxWait;
    private final Semaphore permits;

    public Bulkhead(String name, int maxConcurrent, Duration maxWait) {
        this.name = name;
        this.maxWait = maxWait;
        this.permits = new Semaphore(maxConcurrent);
    }

    public <T> T call(Callable<T> work) throws Exception {
        // 1. wait a bounded time for a slot; a zero wait means "fail fast"
        if (!permits.tryAcquire(maxWait.toNanos(), TimeUnit.NANOSECONDS)) {
            throw new BulkheadFullException("bulkhead '" + name + "' is full");
        }
        try {
            return work.call();          // 2. the call to the downstream system
        } finally {
            permits.release();           // 3. give the slot back, even if the call threw
        }
    }

    public int available() {
        return permits.availablePermits();
    }

    public String name() {
        return name;
    }
}
