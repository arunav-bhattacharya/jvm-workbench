package workbench.ledger.l01;

import java.util.List;
import java.util.function.Function;

/**
 * A load generator that makes threads collide on the ledger on purpose.
 *
 * <p>TODO: write {@link #run}.
 * <ol>
 *   <li>Start {@code threads} threads. Hold each one behind a start line: a
 *       {@code CountDownLatch ready} of size {@code threads} that each thread counts down, and a
 *       {@code CountDownLatch go} of size 1 that each thread awaits. The caller awaits
 *       {@code ready}, then counts down {@code go}.</li>
 *   <li>Each thread makes {@code perThread} random transfers: two different accounts from
 *       {@code accounts}, an amount from 1 to {@code maxCents}, a unique id. Use
 *       {@code ThreadLocalRandom.current()} inside the thread.</li>
 *   <li>Each thread counts its own applied and refused outcomes in local variables, and stores
 *       them in its own slot of a {@code long[]} when it is done. Nothing is shared while it runs.</li>
 *   <li>Join every thread, then add up the slots.</li>
 * </ol>
 */
public final class StressHarness {
    private StressHarness() {}

    /** What one run did. Every transfer is either applied or refused. */
    public record Result(long applied, long refused) {
        public long total() {
            return applied + refused;
        }
    }

    /**
     * Runs {@code threads x perThread} random transfers through {@code ledger}, all threads released
     * at the same moment. Returns after every thread has finished.
     */
    public static Result run(int threads, int perThread, List<String> accounts, long maxCents,
                             Function<Transfer, Outcome> ledger) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: start line, random transfers, per-thread counts, join");
    }
}
