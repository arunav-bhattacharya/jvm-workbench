package workbench.concurrency.l08;

import java.util.concurrent.atomic.AtomicLong;

public class MaxTracker {
    private final AtomicLong max = new AtomicLong(Long.MIN_VALUE);

    public long offer(long amount) {
        while (true) {
            long prev = max.get();                          // 1. read the current max
            if (amount <= prev) return prev;                // 2. not a new max: no write at all
            if (max.compareAndSet(prev, amount)) {          // 3. swap only if nobody changed it since step 1
                return prev;
            }
            // 4. another thread changed it first: loop, read again, decide again
        }
        // the one-line version: return max.getAndAccumulate(amount, Math::max);
    }

    public long max() {
        return max.get();
    }
}
