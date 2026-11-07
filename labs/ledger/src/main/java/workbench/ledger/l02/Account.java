package workbench.ledger.l02;

import java.util.concurrent.locks.ReentrantLock;

/**
 * One account. Its balance is guarded by its own lock: read or change it only while you hold
 * {@link #lock()}. The methods check that you do, so a missing lock fails loudly in the tests
 * instead of losing money quietly in production. You don't need to change this class.
 */
public final class Account {
    private final String id;                              // the key for the global lock order
    private final ReentrantLock lock = new ReentrantLock();
    private long balance;                                 // guarded by lock

    Account(String id, long openingCents) {
        this.id = id;
        this.balance = openingCents;
    }

    public String id() {
        return id;
    }

    public ReentrantLock lock() {
        return lock;
    }

    /** The balance in cents. Hold {@link #lock()} while you call this. */
    public long balance() {
        requireLock();
        return balance;
    }

    void debit(long cents) {
        requireLock();
        // invariant 2, checked where it can break: a race that overdraws fails loudly, at once
        if (cents > balance) throw new IllegalStateException("overdraft on " + id + ": " + balance + " - " + cents);
        balance -= cents;
    }

    void credit(long cents) {
        requireLock();
        balance += cents;
    }

    private void requireLock() {
        if (!lock.isHeldByCurrentThread()) {
            throw new IllegalStateException("take the lock of account " + id + " first");
        }
    }
}
