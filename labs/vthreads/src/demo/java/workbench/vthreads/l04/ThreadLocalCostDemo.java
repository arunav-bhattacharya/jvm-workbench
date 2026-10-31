package workbench.vthreads.l04;

import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.TimeZone;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.LongFunction;
import java.util.function.Supplier;

/**
 * Formats 100,000 receipt timestamps three ways and counts how many formatter objects get built:
 * a ThreadLocal cache on a pool of 8 platform threads, the same cache with one virtual thread per
 * task, and one shared immutable DateTimeFormatter.
 */
public class ThreadLocalCostDemo {
    static final int TASKS = 100_000;
    static final AtomicInteger built = new AtomicInteger();

    // the classic "SimpleDateFormat isn't thread-safe, so keep one per thread" cache
    static final ThreadLocal<SimpleDateFormat> PER_THREAD = ThreadLocal.withInitial(() -> {
        built.incrementAndGet();
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");
        f.setTimeZone(TimeZone.getTimeZone("UTC"));
        return f;
    });

    public static void main(String[] args) {
        run("ThreadLocal cache, pool of 8 platform threads", Executors.newFixedThreadPool(8),
                () -> t -> PER_THREAD.get().format(new Date(t)));
        run("ThreadLocal cache, virtual thread per task", Executors.newVirtualThreadPerTaskExecutor(),
                () -> t -> PER_THREAD.get().format(new Date(t)));
        run("shared DateTimeFormatter, virtual threads", Executors.newVirtualThreadPerTaskExecutor(), () -> {
            built.incrementAndGet();                    // built once, here, and shared by every thread
            DateTimeFormatter shared = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").withZone(ZoneOffset.UTC);
            return t -> shared.format(Instant.ofEpochMilli(t));
        });
    }

    static void run(String label, ExecutorService executor, Supplier<LongFunction<String>> setup) {
        int before = built.get();
        long t0 = System.nanoTime();
        LongFunction<String> stamp = setup.get();
        try (executor) {
            for (int i = 0; i < TASKS; i++) {
                long t = 1_700_000_000_000L + i;
                executor.execute(() -> stamp.apply(t));
            }
        }
        System.out.printf("%-46s formatters built: %,7d   time: %,5d ms%n",
                label, built.get() - before, (System.nanoTime() - t0) / 1_000_000);
    }
}
