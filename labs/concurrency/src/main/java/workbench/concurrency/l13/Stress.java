package workbench.concurrency.l13;

import java.util.function.Consumer;
import java.util.function.Predicate;
import java.util.function.Supplier;

/**
 * A small stress-test harness, shaped like jcstress: a fresh state per round, actors that hit it from
 * many threads at once, and an invariant checked when they are all done.
 */
public final class Stress {
    private Stress() {}

    /**
     * Runs {@code rounds} independent rounds and returns how many of them broke the invariant.
     *
     * <p>Each round:
     * <ol>
     *   <li>makes a fresh state with {@code setup} (called once per round);</li>
     *   <li>starts {@code threads} threads, held behind a start latch until all of them exist, then released together;</li>
     *   <li>each thread calls {@code actor.accept(state)} {@code perThread} times;</li>
     *   <li>waits for every thread to finish;</li>
     *   <li>calls {@code invariant.test(state)} once; {@code false} counts the round as failed.</li>
     * </ol>
     */
    public static <S> int failingRounds(int rounds, int threads, int perThread,
                                        Supplier<S> setup, Consumer<S> actor, Predicate<S> invariant)
            throws InterruptedException {
        throw new UnsupportedOperationException("TODO: per round: setup, start threads behind a latch, release, join, check");
    }
}
