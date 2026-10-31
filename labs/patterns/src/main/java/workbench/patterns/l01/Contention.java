package workbench.patterns.l01;

import java.util.function.Supplier;

/**
 * A small harness that proves (or disproves) "only one instance" under contention.
 *
 * <p>Write {@link #distinctInstances}: start {@code threads} new threads, hold them behind a
 * {@link java.util.concurrent.CountDownLatch} until all of them are ready, release them together,
 * let each call {@code supplier.get()} once, wait for all of them, and return how many different
 * objects came back. "Different" means a different object in memory ({@code ==}), not
 * {@code equals}: two empty lists are equal but they are two instances.
 */
public final class Contention {
    private Contention() {}

    /** How many distinct objects (by identity) {@code threads} simultaneous calls to {@code supplier} returned. */
    public static int distinctInstances(int threads, Supplier<?> supplier) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: start the threads behind a latch, collect results, count by identity");
    }
}
