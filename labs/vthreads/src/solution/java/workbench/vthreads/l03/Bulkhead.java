package workbench.vthreads.l03;

import java.util.concurrent.Callable;
import java.util.concurrent.Semaphore;

public final class Bulkhead {
    private final Semaphore permits;

    public Bulkhead(int maxConcurrent) {
        this.permits = new Semaphore(maxConcurrent);
    }

    public <T> T call(Callable<T> work) throws Exception {
        permits.acquire();          // a virtual thread waiting here is parked: cheap
        try {
            return work.call();
        } finally {
            permits.release();      // always give the slot back, or the bulkhead slowly shrinks to zero
        }
    }

    public int available() {
        return permits.availablePermits();
    }
}
