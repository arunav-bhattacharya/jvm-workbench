package workbench.ledger.l01;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * An in-memory ledger: a fixed set of accounts and a method that moves money between them.
 *
 * <p>Invariants, which the tests check while 8 threads hammer {@link #apply}:
 * <ol>
 *   <li>Money is conserved: the sum of all balances never changes.</li>
 *   <li>No balance ever goes below zero.</li>
 *   <li>A transfer is applied whole or not at all: nobody sees a debit without its credit.</li>
 * </ol>
 */
public final class Ledger {
    // built once in the constructor and never changed afterwards: a final field of an immutable map
    private final Map<String, Account> accounts;
    private final long openingTotal;

    public Ledger(Map<String, Long> openingBalances) {
        Map<String, Account> built = new HashMap<>();
        long total = 0;
        for (Map.Entry<String, Long> e : openingBalances.entrySet()) {
            if (e.getValue() < 0) throw new IllegalArgumentException("negative opening balance for " + e.getKey());
            built.put(e.getKey(), new Account(e.getKey(), e.getValue()));
            total += e.getValue();
        }
        this.accounts = Map.copyOf(built);
        this.openingTotal = total;
    }

    /**
     * Moves {@code t.cents()} from {@code t.from()} to {@code t.to()}, or refuses if the source
     * account holds less than that. Throws {@link IllegalArgumentException} for an unknown account.
     *
     * <p>TODO:
     * <ol>
     *   <li>Look up both accounts with {@link #account}.</li>
     *   <li>Lock them in one global order: the account whose {@code id()} sorts first
     *       ({@code compareTo}) is locked first, whichever way the money moves.</li>
     *   <li>Under both locks, check the balance, then debit and credit. Return the outcome.</li>
     *   <li>Unlock both in {@code finally} blocks, also when you return early.</li>
     * </ol>
     */
    public Outcome apply(Transfer t) {
        throw new UnsupportedOperationException("TODO: lock both accounts in id order, check, move the money");
    }

    /** One account's balance. */
    public long balanceOf(String id) {
        Account a = account(id);
        a.lock().lock();
        try {
            return a.balance();
        } finally {
            a.lock().unlock();
        }
    }

    /**
     * The sum of all balances, read one account at a time. It is exact only when no transfer is
     * running. Lesson 2 builds a snapshot that stays exact while transfers run.
     */
    public long total() {
        long sum = 0;
        for (String id : accountIds()) sum += balanceOf(id);
        return sum;
    }

    /** The total the ledger opened with. Invariant 1 says {@link #total()} always equals it. */
    public long openingTotal() {
        return openingTotal;
    }

    /** Every account id, sorted. */
    public List<String> accountIds() {
        return accounts.keySet().stream().sorted().toList();
    }

    private Account account(String id) {
        Account a = accounts.get(id);
        if (a == null) throw new IllegalArgumentException("unknown account " + id);
        return a;
    }
}
