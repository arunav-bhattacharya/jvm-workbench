package workbench.ledger.l01;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * An in-memory ledger. Invariants: money is conserved, no balance goes below zero, and a transfer
 * is applied whole or not at all.
 */
public final class Ledger {
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

    public Outcome apply(Transfer t) {
        Account from = account(t.from());
        Account to = account(t.to());
        // 1. one global order for every caller: the lower id is locked first, whichever way the money moves
        Account first = from.id().compareTo(to.id()) < 0 ? from : to;
        Account second = first == from ? to : from;
        first.lock().lock();
        try {
            second.lock().lock();
            try {
                // 2. check and act under both locks: nobody can spend this money between the two
                if (from.balance() < t.cents()) return Outcome.INSUFFICIENT_FUNDS;
                // 3. debit and credit in one critical section: no thread ever sees half a transfer
                from.debit(t.cents());
                to.credit(t.cents());
                return Outcome.APPLIED;
            } finally {
                second.lock().unlock();
            }
        } finally {
            first.lock().unlock();   // 4. released on every path, including the early return
        }
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

    public long total() {
        long sum = 0;
        for (String id : accountIds()) sum += balanceOf(id);
        return sum;
    }

    public long openingTotal() {
        return openingTotal;
    }

    public List<String> accountIds() {
        return accounts.keySet().stream().sorted().toList();
    }

    private Account account(String id) {
        Account a = accounts.get(id);
        if (a == null) throw new IllegalArgumentException("unknown account " + id);
        return a;
    }
}
