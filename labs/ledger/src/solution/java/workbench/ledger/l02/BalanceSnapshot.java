package workbench.ledger.l02;

import java.util.Map;

/**
 * Every account's balance at one instant, as one immutable value. You don't need to change it.
 *
 * <p>Safe to hand to any thread, however it is published: the record's fields are final, and
 * {@code balances} is a copy that nobody else holds, made unmodifiable by {@link Map#copyOf}.
 */
public record BalanceSnapshot(Map<String, Long> balances, long total, long version) {
    public BalanceSnapshot {
        balances = Map.copyOf(balances);
    }

    /** The balances added up again. Equals {@link #total()} unless the snapshot is torn. */
    public long sum() {
        return balances.values().stream().mapToLong(Long::longValue).sum();
    }
}
