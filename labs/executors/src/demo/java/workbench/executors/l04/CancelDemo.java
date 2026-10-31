package workbench.executors.l04;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** cancel(true) on three tasks: one that sleeps, one that checks the flag, one that never looks. */
public class CancelDemo {
    // about a second of CPU work, in slices
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
                System.out.println("checker: finished all slices " + (x & 1));
            });
            Future<?> ignorer = pool.submit(() -> {
                long x = 0;
                for (int s = 0; s < 400; s++) x = slice(x);   // never looks at the flag
                System.out.println("ignorer: finished all 400 slices anyway " + (x & 1));
            });

            Thread.sleep(100);
            for (Future<?> f : new Future<?>[] {sleeper, checker, ignorer}) f.cancel(true);
            System.out.printf("after cancel: isCancelled=%b/%b/%b isDone=%b/%b/%b%n",
                    sleeper.isCancelled(), checker.isCancelled(), ignorer.isCancelled(),
                    sleeper.isDone(), checker.isDone(), ignorer.isDone());
        }   // close() waits: the ignorer is still burning CPU
        System.out.println("pool closed");
    }
}
