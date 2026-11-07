package workbench.concurrency.l10;

import java.time.Duration;
import java.util.concurrent.Callable;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class IssuerGate {
    private final Semaphore permits;

    public IssuerGate(int maxConcurrent) {
        this.permits = new Semaphore(maxConcurrent);
    }

    public <T> T call(Callable<T> task) throws Exception {
        permits.acquire();                   // 1. before the try, like lock(): if this throws, we hold nothing
        try {
            return task.call();              // 2. at most maxConcurrent threads are here
        } finally {
            permits.release();               // 3. give back exactly the permit we took
        }
    }

    public <T> T call(Callable<T> task, Duration maxWait) throws Exception {
        if (!permits.tryAcquire(maxWait.toNanos(), TimeUnit.NANOSECONDS)) {
            throw new TimeoutException("no issuer permit within " + maxWait);   // no permit: don't run, don't release
        }
        try {
            return task.call();
        } finally {
            permits.release();
        }
    }

    public int available() {
        return permits.availablePermits();
    }
}
