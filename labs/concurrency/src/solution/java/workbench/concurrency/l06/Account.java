package workbench.concurrency.l06;

import java.util.concurrent.locks.ReentrantLock;

/**
 * A ledger account with its own lock. Given: you don't need to change this class.
 *
 * <p>{@link #debit} and {@link #credit} refuse to run unless the calling thread holds this
 * account's lock, so a transfer that forgets a lock fails loudly instead of racing quietly.
 */
public final class Account {
    private final int id;
    private final ReentrantLock lock = new ReentrantLock();
    private long balanceCents;           // guarded by lock

    public Account(int id, long balanceCents) {
        this.id = id;
        this.balanceCents = balanceCents;
    }

    /** A unique, stable number: use it to decide which lock to take first. */
    public int id() {
        return id;
    }

    public ReentrantLock lock() {
        return lock;
    }

    public void debit(long cents) {
        requireLock();
        balanceCents -= cents;
    }

    public void credit(long cents) {
        requireLock();
        balanceCents += cents;
    }

    public long balanceCents() {
        lock.lock();
        try {
            return balanceCents;
        } finally {
            lock.unlock();
        }
    }

    private void requireLock() {
        if (!lock.isHeldByCurrentThread()) {
            throw new IllegalStateException("lock account " + id + " before changing its balance");
        }
    }
}
