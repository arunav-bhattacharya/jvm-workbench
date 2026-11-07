package workbench.concurrency.l12;

import java.lang.management.ManagementFactory;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Five philosophers, five forks, 200 meals each. Run as is (left fork, then right),
 * with -Pargs=ordered (lower-numbered fork first) or -Pargs=waiter (at most 4 may sit down).
 */
public class Philosophers {
    public static void main(String[] args) throws InterruptedException {
        String mode = args.length > 0 ? args[0] : "naive";
        int n = 5;
        ReentrantLock[] forks = new ReentrantLock[n];
        for (int i = 0; i < n; i++) forks[i] = new ReentrantLock();
        Semaphore seats = new Semaphore(n - 1);                       // the waiter: one chair short
        AtomicInteger meals = new AtomicInteger();

        Thread[] ps = new Thread[n];
        for (int i = 0; i < n; i++) {
            int left = i, right = (i + 1) % n;
            int first = mode.equals("ordered") ? Math.min(left, right) : left;
            int second = mode.equals("ordered") ? Math.max(left, right) : right;
            ps[i] = new Thread(() -> {
                try {
                    for (int m = 0; m < 200; m++) {
                        if (mode.equals("waiter")) seats.acquire();
                        try {
                            forks[first].lock();
                            try {
                                Thread.sleep(1);                      // reach for the other fork
                                forks[second].lock();
                                try { meals.incrementAndGet(); } finally { forks[second].unlock(); }
                            } finally {
                                forks[first].unlock();
                            }
                        } finally {
                            if (mode.equals("waiter")) seats.release();
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "philosopher-" + i);
            ps[i].setDaemon(true);
            ps[i].start();
        }
        long t0 = System.nanoTime();
        long deadline = t0 + 3_000_000_000L;                          // 3 s for the whole table
        for (Thread p : ps) p.join(Math.max(1, (deadline - System.nanoTime()) / 1_000_000));
        long[] stuck = ManagementFactory.getThreadMXBean().findDeadlockedThreads();
        System.out.printf("%s: %d of 1,000 meals in %d ms, deadlocked philosophers: %d%n",
                mode, meals.get(), (System.nanoTime() - t0) / 1_000_000, stuck == null ? 0 : stuck.length);
    }
}
