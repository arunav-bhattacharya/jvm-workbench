package workbench.concurrency.l10;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;
import java.util.function.LongBinaryOperator;
import java.util.function.LongConsumer;

public final class RoundRunner {
    private RoundRunner() {}

    public static void run(int workers, int rounds, LongBinaryOperator step, LongConsumer onRoundTotal)
            throws InterruptedException {
        long[] shares = new long[workers];           // each slot is written by one worker only
        // 1. the barrier action runs once per round, on the last worker to arrive, before anyone is released.
        //    Every write a worker made before await() is visible to it.
        CyclicBarrier endOfRound = new CyclicBarrier(workers, () -> {
            long total = 0;
            for (long s : shares) total += s;
            onRoundTotal.accept(total);
        });
        List<Thread> threads = new ArrayList<>();
        for (int w = 0; w < workers; w++) {
            int me = w;
            Thread t = new Thread(() -> {
                try {
                    for (int r = 0; r < rounds; r++) {
                        shares[me] = step.applyAsLong(me, r);   // 2. do this round's share
                        endOfRound.await();                     // 3. wait for the others; the barrier resets itself
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } catch (BrokenBarrierException e) {
                    // another worker failed or was interrupted; stop too
                }
            }, "sim-worker-" + w);
            t.start();
            threads.add(t);
        }
        for (Thread t : threads) t.join();               // 4. return when every round is done
    }
}
