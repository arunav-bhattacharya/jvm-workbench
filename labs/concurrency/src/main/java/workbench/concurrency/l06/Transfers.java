package workbench.concurrency.l06;

import java.time.Duration;

/**
 * Moves money between two accounts while holding both accounts' locks.
 *
 * <p>Part 1: {@link #transfer} deadlocks when two threads move money in opposite directions
 * between the same two accounts. Fix it by always taking the locks in one global order
 * (lowest {@link Account#id()} first), whatever the direction of the transfer.
 *
 * <p>Part 2: write {@link #tryTransfer}, which never waits forever. It uses
 * {@code tryLock} with a short timeout, lets go of everything when it can't get both locks,
 * backs off for a short random time, and tries again until {@code timeout} has passed.
 */
public final class Transfers {
    private Transfers() {}

    public static void transfer(Account from, Account to, long cents) {
        from.lock().lock();                 // the order depends on the direction of the transfer...
        try {
            to.lock().lock();               // ...so A->B and B->A take the same two locks in opposite orders
            try {
                from.debit(cents);
                to.credit(cents);
            } finally {
                to.lock().unlock();
            }
        } finally {
            from.lock().unlock();
        }
    }

    /**
     * Moves {@code cents} if it can hold both locks before {@code timeout} runs out.
     * Returns true if the money moved, false if it gave up. Either way it holds no lock when it returns.
     */
    public static boolean tryTransfer(Account from, Account to, long cents, Duration timeout) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: tryLock both with a short timeout, release on failure, back off, retry until the deadline");
    }
}
