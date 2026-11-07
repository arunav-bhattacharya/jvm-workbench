package workbench.concurrency.l10;

import java.util.function.LongBinaryOperator;
import java.util.function.LongConsumer;

/**
 * Runs an end-of-day exposure simulation in rounds (one round per simulated day) on {@code workers}
 * threads. Each worker owns one slice of the accounts.
 *
 * <ul>
 *   <li>In each round, every worker computes its share: {@code step.applyAsLong(worker, round)}.</li>
 *   <li>When all workers have finished a round, the round's total (the sum of the shares) is passed to
 *       {@code onRoundTotal}, exactly once per round, in round order.</li>
 *   <li>No worker starts round {@code r + 1} before the total for round {@code r} has been passed on.</li>
 *   <li>{@code run} returns after every round is done.</li>
 * </ul>
 * Use one {@link java.util.concurrent.CyclicBarrier} with a barrier action. Workers are numbered from 0.
 */
public final class RoundRunner {
    private RoundRunner() {}

    public static void run(int workers, int rounds, LongBinaryOperator step, LongConsumer onRoundTotal)
            throws InterruptedException {
        throw new UnsupportedOperationException(
                "TODO: a CyclicBarrier(workers, action) whose action sums the shares; each worker loops: compute, await");
    }
}
