package workbench.ledger.l03;

import java.time.Duration;

public record PoolPlan(int threads, int queueCapacity) {
    public PoolPlan {
        if (threads < 1) throw new IllegalArgumentException("threads must be at least 1: " + threads);
        if (queueCapacity < 1) throw new IllegalArgumentException("queueCapacity must be at least 1: " + queueCapacity);
    }

    public static PoolPlan fromLittlesLaw(int perSecond, Duration timePerTransfer, Duration maxQueueWait) {
        // L = lambda x W, in whole nanoseconds so 8.0 stays 8
        long threads = Math.ceilDiv(perSecond * timePerTransfer.toNanos(), 1_000_000_000L);
        // a full queue of perSecond x maxWait drains in maxWait when the pool finishes perSecond a second
        long queue = Math.ceilDiv(perSecond * maxQueueWait.toNanos(), 1_000_000_000L);
        return new PoolPlan((int) Math.max(1, threads), (int) Math.max(1, queue));
    }
}
