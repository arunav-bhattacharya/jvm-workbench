package workbench.concurrency.l13;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.function.Consumer;
import java.util.function.Predicate;
import java.util.function.Supplier;

public final class Stress {
    private Stress() {}

    public static <S> int failingRounds(int rounds, int threads, int perThread,
                                        Supplier<S> setup, Consumer<S> actor, Predicate<S> invariant)
            throws InterruptedException {
        int failed = 0;
        for (int round = 0; round < rounds; round++) {
            S state = setup.get();                                  // 1. fresh state: rounds can't affect each other
            CountDownLatch ready = new CountDownLatch(threads);
            CountDownLatch go = new CountDownLatch(1);
            List<Thread> started = new ArrayList<>();
            for (int t = 0; t < threads; t++) {
                Thread th = new Thread(() -> {
                    ready.countDown();
                    try {
                        go.await();                                 // 2. everyone waits at the start line
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                    for (int i = 0; i < perThread; i++) actor.accept(state);   // 3. collide
                }, "stress-" + round + "-" + t);
                th.setDaemon(true);                                 // a stuck actor must not keep the JVM alive
                th.start();
                started.add(th);
            }
            ready.await();
            go.countDown();                                         // release them together
            for (Thread th : started) th.join();                    // 4. join: their writes are now visible here
            if (!invariant.test(state)) failed++;                   // 5. check once, after the dust settles
        }
        return failed;
    }
}
