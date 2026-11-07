package workbench.vthreads.l06;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.LongAdder;
import java.util.concurrent.locks.LockSupport;

/**
 * Requests arrive at a steady rate, one virtual thread each. A request waits for one of 10
 * database permits, runs a 20 ms query, then makes a 100 ms FX call. A sampler prints two
 * gauges you would put on a dashboard, and the summary checks Little's law:
 * requests in flight = throughput x time in the system.
 *
 * <p>Args: requests per second (default 400), seconds (default 2).
 */
public class MeasureDemo {
    static final Semaphore dbPermits = new Semaphore(10, true);
    static final AtomicInteger inFlight = new AtomicInteger();
    static final LongAdder done = new LongAdder();
    static final LongAdder nanosInSystem = new LongAdder();
    static volatile boolean stop;

    static void handle() {
        long start = System.nanoTime();
        inFlight.incrementAndGet();
        try {
            dbPermits.acquire();
            try {
                Thread.sleep(20);                                // the database query
            } finally {
                dbPermits.release();
            }
            Thread.sleep(100);                                   // the FX call
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            inFlight.decrementAndGet();
            nanosInSystem.add(System.nanoTime() - start);
            done.increment();
        }
    }

    public static void main(String[] args) throws Exception {
        int rate = args.length > 0 ? Integer.parseInt(args[0]) : 400;
        int seconds = args.length > 1 ? Integer.parseInt(args[1]) : 2;
        long gapNanos = 1_000_000_000L / rate;
        long t0 = System.nanoTime();

        // sample every 10 ms for the average; print every 250 ms
        long[] sums = new long[2];                                // total in flight, number of samples
        Thread sampler = Thread.ofPlatform().daemon().start(() -> {
            while (!stop) {
                LockSupport.parkNanos(10_000_000);
                sums[0] += inFlight.get();
                sums[1]++;
                if (sums[1] % 25 == 0) {
                    System.out.printf("t=%,5d ms   in flight %4d   waiting for a db permit %4d%n",
                            (System.nanoTime() - t0) / 1_000_000, inFlight.get(), dbPermits.getQueueLength());
                }
            }
        });

        try (ExecutorService perRequest = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < rate * seconds; i++) {
                long due = t0 + i * gapNanos, wait;
                while ((wait = due - System.nanoTime()) > 0) LockSupport.parkNanos(wait);   // steady arrivals
                perRequest.execute(MeasureDemo::handle);
            }
        }                                                         // waits for the last requests
        double elapsed = (System.nanoTime() - t0) / 1e9;
        stop = true;
        sampler.join();

        double throughput = done.sum() / elapsed;                 // requests per second
        double timeInSystem = nanosInSystem.sum() / 1e9 / done.sum();
        System.out.printf("throughput %.0f/s, mean time in system %.0f ms%n", throughput, timeInSystem * 1000);
        System.out.printf("Little's law: throughput x time = %.1f; measured average in flight = %.1f%n",
                throughput * timeInSystem, (double) sums[0] / sums[1]);
    }
}
