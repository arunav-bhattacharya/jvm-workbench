package workbench.ledger.l01.demo;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ThreadLocalRandom;

/** A ledger with no locks: 8 threads move money between 50 accounts. Count what goes wrong. */
public class BrokenLedgerDemo {
    static final int ACCOUNTS = 50;
    static final long OPENING = 10_000;              // cents per account: 500,000 in total

    public static void main(String[] args) throws InterruptedException {
        int perThread = args.length > 0 ? Integer.parseInt(args[0]) : 100_000;
        for (int run = 1; run <= 3; run++) {
            long[] balance = new long[ACCOUNTS];
            Arrays.fill(balance, OPENING);
            CountDownLatch go = new CountDownLatch(1);
            List<Thread> workers = new ArrayList<>();
            for (int i = 0; i < 8; i++) {
                Thread w = new Thread(() -> {
                    ThreadLocalRandom rnd = ThreadLocalRandom.current();
                    try { go.await(); } catch (InterruptedException e) { return; }
                    for (int n = 0; n < perThread; n++) {
                        int from = rnd.nextInt(ACCOUNTS), to = rnd.nextInt(ACCOUNTS);
                        if (from == to) continue;
                        long cents = 1 + rnd.nextLong(5_000);
                        if (balance[from] >= cents) {     // check
                            balance[from] -= cents;       // act: read, subtract, write
                            balance[to] += cents;         //      read, add, write
                        }
                    }
                });
                w.start();
                workers.add(w);
            }
            go.countDown();
            for (Thread w : workers) w.join();
            long total = 0;
            for (long b : balance) total += b;
            System.out.printf("run %d: total %,d cents, expected 500,000, off by %,d%n",
                    run, total, total - ACCOUNTS * OPENING);
        }
    }
}
