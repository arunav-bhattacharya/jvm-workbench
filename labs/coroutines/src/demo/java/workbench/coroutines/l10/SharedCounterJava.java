// Java equivalent of SharedCounter.kt: the same counter on 8 platform threads. Coroutines on
// Dispatchers.Default run in parallel, so they race exactly like threads do.
package workbench.coroutines.l10;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.LongSupplier;

public class SharedCounterJava {
    static long plain = 0;
    static volatile long volatileCount = 0;
    static long guarded = 0;

    static void count(String label, Runnable increment, LongSupplier read) {
        long t0 = System.nanoTime();
        try (ExecutorService pool = Executors.newFixedThreadPool(8)) {
            for (int t = 0; t < 100; t++) pool.submit(() -> { for (int i = 0; i < 10_000; i++) increment.run(); });
        }
        System.out.printf("%-28s %,9d of 1,000,000 in %4d ms%n", label, read.getAsLong(), (System.nanoTime() - t0) / 1_000_000);
    }

    public static void main(String[] args) {
        count("plain field", () -> plain++, () -> plain);
        count("volatile field", () -> volatileCount++, () -> volatileCount);
        AtomicLong atomic = new AtomicLong();
        count("AtomicLong", atomic::incrementAndGet, atomic::get);
        ReentrantLock lock = new ReentrantLock();
        count("ReentrantLock", () -> { lock.lock(); try { guarded++; } finally { lock.unlock(); } }, () -> guarded);
    }
}
