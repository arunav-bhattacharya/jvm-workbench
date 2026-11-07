package workbench.ledger.l03.demo;

import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

/** 400 requests a second for 3 seconds, each on its own virtual thread. Pass "outage" to slow the fraud service to 2 s. */
public class FraudOutageDemoJava {
    static final long BUDGET_NANOS = 300_000_000L;          // every request answers within 300 ms
    static final long STAND_IN_CENTS = 5_000L;              // stand-in limit: up to 50.00 goes through unchecked
    static final Semaphore permits = new Semaphore(20);     // the fraud bulkhead
    static final AtomicInteger inFlight = new AtomicInteger(), mostInFlight = new AtomicInteger();
    static final Map<String, LongAdder> verdicts = new ConcurrentHashMap<>();
    static final AtomicLong slowestMs = new AtomicLong();

    // the fraud call, on its own virtual thread: a permit first, then the remote call
    static boolean fraudCall(long latencyMs, long deadline) throws Exception {
        if (!permits.tryAcquire(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)) throw new TimeoutException("no permit");
        try {
            mostInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
            try {
                Thread.sleep(latencyMs);                    // the fraud service; an interrupt ends it early
            } finally {
                inFlight.decrementAndGet();
            }
            return true;
        } finally {
            permits.release();
        }
    }

    static String screen(long cents, long latencyMs) throws InterruptedException {
        long deadline = System.nanoTime() + BUDGET_NANOS;
        try (ExecutorService perCall = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<Boolean> call = perCall.submit(() -> fraudCall(latencyMs, deadline));
            try {
                return call.get(deadline - System.nanoTime(), TimeUnit.NANOSECONDS) ? "approved" : "declined";
            } catch (TimeoutException e) {                  // our deadline passed first
                call.cancel(true);                          // interrupt the call: it holds a permit
                return fallback(cents);
            } catch (ExecutionException e) {                // no permit before the deadline
                return fallback(cents);
            }
        }
    }

    static String fallback(long cents) {
        return cents <= STAND_IN_CENTS ? "stand-in" : "timed out";
    }

    public static void main(String[] args) throws InterruptedException {
        long latencyMs = args.length > 0 && args[0].equals("outage") ? 2_000 : 20;
        try (ExecutorService perRequest = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int round = 0; round < 300; round++) {     // 300 rounds of 4 requests, 10 ms apart
                for (int i = 0; i < 4; i++) {
                    long cents = 1 + ThreadLocalRandom.current().nextLong(20_000);
                    perRequest.execute(() -> {
                        long t0 = System.nanoTime();
                        try {
                            verdicts.computeIfAbsent(screen(cents, latencyMs), k -> new LongAdder()).increment();
                        } catch (InterruptedException e) {
                            return;
                        }
                        slowestMs.accumulateAndGet((System.nanoTime() - t0) / 1_000_000, Math::max);
                    });
                }
                Thread.sleep(10);
            }
        }
        System.out.printf("fraud service takes %d ms: %s%n", latencyMs, new TreeMap<>(verdicts));
        System.out.printf("most fraud calls in flight: %d, slowest reply: %d ms%n", mostInFlight.get(), slowestMs.get());
    }
}
