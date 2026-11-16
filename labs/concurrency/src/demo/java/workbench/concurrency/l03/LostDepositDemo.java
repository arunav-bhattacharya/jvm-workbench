package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Eight teller threads put one-cent deposits into the same bank account, three ways. */
public class LostDepositDemo {
    static final int THREADS = 8;
    static final int DEPOSITS = 200_000;                     // per thread, one cent each
    static final String ACCOUNT = "account-42";

    // volatile only so the JIT re-reads the field every time, as in RaceDemo. It does NOT make += safe.
    static volatile long balanceCents;
    static final Map<String, Long> balances = new ConcurrentHashMap<>();

    public static void main(String[] args) throws InterruptedException {
        balanceCents = 0;
        runTellers(() -> balanceCents += 1);                                  // 1. a plain field
        report("balanceCents += 1", balanceCents);

        balances.put(ACCOUNT, 0L);
        runTellers(() -> balances.put(ACCOUNT, balances.get(ACCOUNT) + 1));   // 2. a thread-safe map, two calls
        report("put(get() + 1)", balances.get(ACCOUNT));

        balances.put(ACCOUNT, 0L);
        runTellers(() -> balances.merge(ACCOUNT, 1L, Long::sum));             // 3. the same map, one call
        report("merge(1, Long::sum)", balances.get(ACCOUNT));
    }

    static void runTellers(Runnable deposit) throws InterruptedException {
        Thread[] tellers = new Thread[THREADS];
        for (int c = 0; c < THREADS; c++) {
            tellers[c] = new Thread(() -> {
                for (int i = 0; i < DEPOSITS; i++) deposit.run();
            }, "teller-" + c);
            tellers[c].start();
        }
        for (Thread t : tellers) t.join();
    }

    static void report(String how, long cents) {
        long expected = (long) THREADS * DEPOSITS;
        System.out.printf("%-20s expected %,d cents, got %,d (lost %,d)%n", how, expected, cents, expected - cents);
    }
}
