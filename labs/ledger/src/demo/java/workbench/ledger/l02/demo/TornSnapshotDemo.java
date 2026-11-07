package workbench.ledger.l02.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Four threads move money between 50 accounts while a reader adds up all the balances.
 * Pass "locked" to make the reader hold every account lock while it adds.
 */
public class TornSnapshotDemo {
    static final class Account {
        final int id;
        final ReentrantLock lock = new ReentrantLock();
        long balance = 1_000;                                 // guarded by lock: 50,000 in total

        Account(int id) { this.id = id; }
    }

    public static void main(String[] args) throws InterruptedException {
        boolean locked = args.length > 0 && args[0].equals("locked");
        Account[] accounts = new Account[50];
        for (int i = 0; i < accounts.length; i++) accounts[i] = new Account(i);
        AtomicBoolean writing = new AtomicBoolean(true);
        List<Thread> writers = new ArrayList<>();
        for (int w = 0; w < 4; w++) {
            writers.add(Thread.ofPlatform().start(() -> {
                ThreadLocalRandom rnd = ThreadLocalRandom.current();
                for (int n = 0; n < 200_000; n++) {
                    int a = rnd.nextInt(50), b = rnd.nextInt(49);
                    if (b >= a) b++;
                    move(accounts[a], accounts[b], 1 + rnd.nextLong(500));
                }
            }));
        }
        long taken = 0, torn = 0, worst = 0;
        while (writers.stream().anyMatch(Thread::isAlive)) {
            long sum = locked ? sumAllLocked(accounts) : sumOneByOne(accounts);
            taken++;
            if (sum != 50_000) {
                torn++;
                worst = Math.max(worst, Math.abs(sum - 50_000));
            }
        }
        System.out.printf("%s: %,d snapshots, %,d torn (worst off by %,d cents)%n",
                locked ? "every lock held" : "one account at a time", taken, torn, worst);
    }

    // each read is safe on its own; the sum is not, because money moves between reads
    static long sumOneByOne(Account[] accounts) {
        long sum = 0;
        for (Account a : accounts) {
            a.lock.lock();
            try { sum += a.balance; } finally { a.lock.unlock(); }
        }
        return sum;
    }

    // every lock, in id order: no transfer can run while we add, so the sum is one instant
    static long sumAllLocked(Account[] accounts) {
        for (Account a : accounts) a.lock.lock();
        try {
            long sum = 0;
            for (Account a : accounts) sum += a.balance;
            return sum;
        } finally {
            for (int i = accounts.length - 1; i >= 0; i--) accounts[i].lock.unlock();
        }
    }

    static void move(Account from, Account to, long cents) {
        Account first = from.id < to.id ? from : to, second = first == from ? to : from;
        first.lock.lock();
        try {
            second.lock.lock();
            try {
                if (from.balance >= cents) { from.balance -= cents; to.balance += cents; }
            } finally {
                second.lock.unlock();
            }
        } finally {
            first.lock.unlock();
        }
    }
}
