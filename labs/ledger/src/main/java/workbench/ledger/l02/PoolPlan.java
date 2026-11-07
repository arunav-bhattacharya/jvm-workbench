package workbench.ledger.l02;

import java.time.Duration;

/** How big the ledger pool is: worker threads and queue slots. */
public record PoolPlan(int threads, int queueCapacity) {
    public PoolPlan {
        if (threads < 1) throw new IllegalArgumentException("threads must be at least 1: " + threads);
        if (queueCapacity < 1) throw new IllegalArgumentException("queueCapacity must be at least 1: " + queueCapacity);
    }

    /**
     * Sizes the pool with Little's law, L = arrival rate x time in the system.
     *
     * <p>TODO:
     * <ul>
     *   <li>threads = {@code perSecond x timePerTransfer}: the transfers in flight at the peak rate,
     *       each holding a thread for {@code timePerTransfer}.</li>
     *   <li>queueCapacity = {@code perSecond x maxQueueWait}: at the peak rate the pool finishes
     *       {@code perSecond} transfers a second, so a full queue of that size drains in exactly
     *       {@code maxQueueWait}.</li>
     * </ul>
     * Round both up and never go below 1. Compute in nanoseconds with {@code long} arithmetic and
     * {@code Math.ceilDiv(..., 1_000_000_000L)}: floating point can turn 8.0 into 8.000000000000002,
     * which rounds up to 9.
     */
    public static PoolPlan fromLittlesLaw(int perSecond, Duration timePerTransfer, Duration maxQueueWait) {
        throw new UnsupportedOperationException("TODO: threads = rate x time per transfer, queue = rate x max wait");
    }
}
