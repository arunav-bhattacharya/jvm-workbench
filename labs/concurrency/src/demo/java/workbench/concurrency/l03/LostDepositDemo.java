package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Eight consumer threads post one-cent deposits to the same merchant account, three ways. */
public class LostDepositDemo {
    static final int THREADS = 8;
    static final int DEPOSITS = 200_000;                     // per thread, one cent each
    static final String MERCHANT = "merchant-42";

    // volatile only so the JIT re-reads the field every time, as in RaceDemo. It does NOT make += safe.
    static volatile long balanceCents;
    static final Map<String, Long> balances = new ConcurrentHashMap<>();

    public static void main(String[] args) throws InterruptedException {
        balanceCents = 0;
        post(() -> balanceCents += 1);                                     // 1. a plain field
        report("balanceCents += 1", balanceCents);

        balances.put(MERCHANT, 0L);
        post(() -> balances.put(MERCHANT, balances.get(MERCHANT) + 1));   // 2. a thread-safe map, two calls
        report("put(get() + 1)", balances.get(MERCHANT));

        balances.put(MERCHANT, 0L);
        post(() -> balances.merge(MERCHANT, 1L, Long::sum));              // 3. the same map, one call
        report("merge(1, Long::sum)", balances.get(MERCHANT));
    }

    static void post(Runnable deposit) throws InterruptedException {
        Thread[] consumers = new Thread[THREADS];
        for (int c = 0; c < THREADS; c++) {
            consumers[c] = new Thread(() -> {
                for (int i = 0; i < DEPOSITS; i++) deposit.run();
            }, "consumer-" + c);
            consumers[c].start();
        }
        for (Thread t : consumers) t.join();
    }

    static void report(String how, long cents) {
        long expected = (long) THREADS * DEPOSITS;
        System.out.printf("%-20s expected %,d cents, got %,d (lost %,d)%n", how, expected, cents, expected - cents);
    }
}
