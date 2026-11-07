package workbench.ledger.l02;

import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * The ledger from lesson 1, plus a balance snapshot that stays exact while transfers run.
 *
 * <p>Who guards what (the happens-before edge for every field):
 * <ul>
 *   <li>{@code accounts}, {@code inLockOrder}, {@code openingTotal}: final fields set in the
 *       constructor and never changed. Any thread that sees the Ledger sees them.</li>
 *   <li>each {@code Account.balance}: that account's lock (an unlock happens-before the next lock).</li>
 *   <li>{@code version}: written only by {@link #snapshot()}, while it holds every account lock.</li>
 *   <li>{@code latest}: volatile. Writing it publishes a whole, immutable snapshot to every reader.</li>
 * </ul>
 */
public final class Ledger {
    private final Map<String, Account> accounts;
    private final List<Account> inLockOrder;      // every account, sorted by id: the global lock order
    private final long openingTotal;
    private long version;                          // guarded by: all account locks held
    private volatile BalanceSnapshot latest;       // the newest published snapshot

    public Ledger(Map<String, Long> openingBalances) {
        Map<String, Account> built = new HashMap<>();
        long total = 0;
        for (Map.Entry<String, Long> e : openingBalances.entrySet()) {
            if (e.getValue() < 0) throw new IllegalArgumentException("negative opening balance for " + e.getKey());
            built.put(e.getKey(), new Account(e.getKey(), e.getValue()));
            total += e.getValue();
        }
        this.accounts = Map.copyOf(built);
        this.inLockOrder = built.values().stream().sorted(Comparator.comparing(Account::id)).toList();
        this.openingTotal = total;
        this.latest = new BalanceSnapshot(openingBalances, total, 0);   // version 0: the opening balances
    }

    /** Lesson 1's apply: two locks in id order, check and move under both. */
    public Outcome apply(Transfer t) {
        Account from = account(t.from());
        Account to = account(t.to());
        Account first = from.id().compareTo(to.id()) < 0 ? from : to;
        Account second = first == from ? to : from;
        first.lock().lock();
        try {
            second.lock().lock();
            try {
                if (from.balance() < t.cents()) return Outcome.INSUFFICIENT_FUNDS;
                from.debit(t.cents());
                to.credit(t.cents());
                return Outcome.APPLIED;
            } finally {
                second.lock().unlock();
            }
        } finally {
            first.lock().unlock();
        }
    }

    /**
     * Takes a snapshot that is exact even while transfers run, publishes it as {@link #latestSnapshot()},
     * and returns it.
     *
     * <p>TODO:
     * <ol>
     *   <li>Lock every account in {@code inLockOrder}, in that order. Now no transfer can move money.</li>
     *   <li>Copy each balance into a map and add up the total.</li>
     *   <li>Build a {@code BalanceSnapshot} with {@code ++version}, and write it to {@code latest}
     *       before you release anything, so snapshots are published in version order.</li>
     *   <li>In a {@code finally}, release the locks in reverse order.</li>
     * </ol>
     * Reading the accounts one at a time, each under its own lock, is not enough: a transfer can
     * move money from an account you have not read yet to one you already have.
     */
    public BalanceSnapshot snapshot() {
        throw new UnsupportedOperationException("TODO: lock every account in id order, copy, publish, release");
    }

    /** The newest published snapshot, read without any lock. It may be older than the live balances. */
    public BalanceSnapshot latestSnapshot() {
        return latest;
    }

    public long balanceOf(String id) {
        Account a = account(id);
        a.lock().lock();
        try {
            return a.balance();
        } finally {
            a.lock().unlock();
        }
    }

    public long openingTotal() {
        return openingTotal;
    }

    public List<String> accountIds() {
        return inLockOrder.stream().map(Account::id).toList();
    }

    private Account account(String id) {
        Account a = accounts.get(id);
        if (a == null) throw new IllegalArgumentException("unknown account " + id);
        return a;
    }
}
