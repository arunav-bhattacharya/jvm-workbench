package workbench.executors.l04;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** cancel(true) on three tasks: one that sleeps, one that checks the flag, one that never looks. */
public class CancelDemo {
    static volatile long sink;          // keeps each result, so the JIT can't skip the work
    static volatile long cancelledAt;   // when main called cancel, for the ignorer's report

    // a few milliseconds of CPU work: 400 of them take a second or more
    static long slice(long x) {
        for (int i = 0; i < 2_000_000; i++) x = x * 31 + i;
        return x;
    }

    public static void main(String[] args) throws Exception {
        try (ExecutorService pool = Executors.newFixedThreadPool(3)) {
            Future<?> sleeper = pool.submit(() -> {
                try {
                    Thread.sleep(5_000);
                    System.out.println("sleeper: woke up normally");
                } catch (InterruptedException e) {
                    System.out.println("sleeper: InterruptedException, stopping");
                }
            });
            Future<?> checker = pool.submit(() -> {
                long x = 0;
                for (int s = 0; s < 400; s++) {
                    if (Thread.currentThread().isInterrupted()) {
                        System.out.println("checker: saw the flag after " + s + " slices, stopping");
                        return;
                    }
                    x = slice(x);
                }
                sink = x;
                System.out.println("checker: finished all 400 slices");
            });
            Future<?> ignorer = pool.submit(() -> {
                long x = 0;
                for (int s = 0; s < 400; s++) x = slice(x);   // never looks at the flag
                sink = x;
                long late = (System.nanoTime() - cancelledAt) / 1_000_000;
                System.out.println("ignorer: finished all 400 slices anyway, " + late + " ms after the cancel");
            });

            Thread.sleep(100);
            cancelledAt = System.nanoTime();
            for (Future<?> f : new Future<?>[] {sleeper, checker, ignorer}) f.cancel(true);
            System.out.printf("after cancel: isCancelled=%b/%b/%b isDone=%b/%b/%b%n",
                    sleeper.isCancelled(), checker.isCancelled(), ignorer.isCancelled(),
                    sleeper.isDone(), checker.isDone(), ignorer.isDone());
        }   // close() waits: the ignorer is still burning CPU
        System.out.println("pool closed");
    }
}
