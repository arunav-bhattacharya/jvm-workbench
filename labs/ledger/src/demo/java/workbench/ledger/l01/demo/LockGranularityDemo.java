package workbench.ledger.l01.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

/** The same random transfers under one ledger-wide lock, then under per-account locks taken in id order. */
public class LockGranularityDemo {
    static final int ACCOUNTS = 50;

    static final class Account {
        final int id;
        final ReentrantLock lock = new ReentrantLock();
        long balance = 10_000;                       // guarded by lock (or by the global lock)

        Account(int id) { this.id = id; }
    }

    interface Mover { void move(Account from, Account to, long cents); }

    static final AtomicInteger inside = new AtomicInteger();    // transfers inside a critical section right now
    static final AtomicInteger mostInside = new AtomicInteger();

    public static void main(String[] args) throws InterruptedException {
        int work = args.length > 0 ? Integer.parseInt(args[0]) : 50;   // extra steps inside the lock, per transfer
        ReentrantLock global = new ReentrantLock();
        Mover oneLock = (from, to, cents) -> {
            global.lock();                           // every transfer waits for every other one
            try {
                if (from.balance >= cents) { from.balance -= cents; to.balance += cents; }
                sign(work);                          // stands in for real work: an entry, a signature
            } finally {
                global.unlock();
            }
        };
        Mover perAccount = (from, to, cents) -> {
            Account first = from.id < to.id ? from : to;   // lower id first: no cycle can form
            Account second = first == from ? to : from;
            first.lock.lock();
            try {
                second.lock.lock();
                try {
                    if (from.balance >= cents) { from.balance -= cents; to.balance += cents; }
                    sign(work);
                } finally {
                    second.lock.unlock();
                }
            } finally {
                first.lock.unlock();
            }
        };
        System.out.printf("8 threads x 50,000 transfers, %d accounts, %d steps of work inside the lock%n", ACCOUNTS, work);
        for (int round = 0; round < 3; round++) {    // round 0 only warms up the JIT
            time("one ledger lock  ", oneLock, round > 0);
            time("per-account locks", perAccount, round > 0);
        }
    }

    static void sign(int steps) {
        int now = inside.incrementAndGet();
        mostInside.accumulateAndGet(now, Math::max);
        for (int i = 0; i < steps; i++) Thread.onSpinWait();
        inside.decrementAndGet();
    }

    static void time(String label, Mover mover, boolean print) throws InterruptedException {
        Account[] accounts = new Account[ACCOUNTS];
        for (int i = 0; i < ACCOUNTS; i++) accounts[i] = new Account(i);
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread w = new Thread(() -> {
                ThreadLocalRandom rnd = ThreadLocalRandom.current();
                try { go.await(); } catch (InterruptedException e) { return; }
                for (int n = 0; n < 50_000; n++) {
                    int a = rnd.nextInt(ACCOUNTS), b = rnd.nextInt(ACCOUNTS - 1);
                    if (b >= a) b++;
                    mover.move(accounts[a], accounts[b], 1 + rnd.nextLong(5_000));
                }
            });
            w.start();
            workers.add(w);
        }
        long t0 = System.nanoTime();
        go.countDown();
        for (Thread w : workers) w.join();
        long ms = (System.nanoTime() - t0) / 1_000_000;
        long total = 0;
        for (Account a : accounts) total += a.balance;   // after join(): every write is visible
        if (print) System.out.printf("%s %5d ms, total %,d, most transfers in progress at once: %d%n",
                label, ms, total, mostInside.get());
        mostInside.set(0);
    }
}
