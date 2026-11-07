package workbench.ledger.l01.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Two ledgers that both lock accounts in id order. One checks the balance before it takes the
 * locks, the other checks after. Run each under 8 threads and test every invariant.
 */
public class CheckOutsideLockDemo {
    static final int ACCOUNTS = 50;
    static final AtomicInteger overdrafts = new AtomicInteger();   // debits that left a balance below zero

    static final class Account {
        final int id;
        final ReentrantLock lock = new ReentrantLock();
        long balance = 10_000;                       // guarded by lock

        Account(int id) { this.id = id; }

        long read() {
            lock.lock();
            try { return balance; } finally { lock.unlock(); }
        }
    }

    // the bug: the check runs under from's lock, but that lock is released before the move
    static void checkFirst(Account from, Account to, long cents) {
        if (from.read() < cents) return;             // check
        lookUpFee();                                 // a slow step, outside any lock
        locked(from, to, () -> move(from, to, cents));   // act, later
    }

    // the fix: check and act inside the same two locks
    static void checkInside(Account from, Account to, long cents) {
        lookUpFee();                                 // the same slow step, still outside the locks
        locked(from, to, () -> {
            if (from.balance >= cents) move(from, to, cents);
        });
    }

    static void move(Account from, Account to, long cents) {
        from.balance -= cents;
        to.balance += cents;
        if (from.balance < 0) overdrafts.incrementAndGet();   // the invariant, checked at the moment it can break
    }

    // stands in for a call to a fee table; it widens the gap between check and act
    static void lookUpFee() {
        for (int i = 0; i < 200; i++) Thread.onSpinWait();
    }

    static void locked(Account a, Account b, Runnable body) {
        Account first = a.id < b.id ? a : b, second = first == a ? b : a;
        first.lock.lock();
        try {
            second.lock.lock();
            try { body.run(); } finally { second.lock.unlock(); }
        } finally {
            first.lock.unlock();
        }
    }

    interface Mover { void move(Account from, Account to, long cents); }

    public static void main(String[] args) throws InterruptedException {
        runVariant("check, then lock and move", CheckOutsideLockDemo::checkFirst);
        runVariant("lock, then check and move", CheckOutsideLockDemo::checkInside);
    }

    static void runVariant(String label, Mover mover) throws InterruptedException {
        Account[] accounts = new Account[ACCOUNTS];
        for (int i = 0; i < ACCOUNTS; i++) accounts[i] = new Account(i);
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread w = new Thread(() -> {
                ThreadLocalRandom rnd = ThreadLocalRandom.current();
                try { go.await(); } catch (InterruptedException e) { return; }
                for (int n = 0; n < 100_000; n++) {
                    int a = rnd.nextInt(ACCOUNTS), b = rnd.nextInt(ACCOUNTS - 1);
                    if (b >= a) b++;
                    mover.move(accounts[a], accounts[b], 1 + rnd.nextLong(5_000));
                }
            });
            w.start();
            workers.add(w);
        }
        go.countDown();
        for (Thread w : workers) w.join();
        long total = 0, negative = 0;
        for (Account a : accounts) {
            total += a.balance;
            if (a.balance < 0) negative++;
        }
        System.out.printf("%s%n  total %,d %s, negative at the end: %d, overdrafts while running: %,d%n",
                label, total, total == 500_000 ? "(conserved)" : "(WRONG)", negative, overdrafts.getAndSet(0));
    }
}
