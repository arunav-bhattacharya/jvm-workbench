package workbench.ledger.l03;

import java.util.Objects;

/**
 * One request to move {@code cents} from account {@code from} to account {@code to}.
 * Immutable: built on one thread, read on many.
 */
public record Transfer(String id, String from, String to, long cents) {
    // the compact constructor runs before the fields are set: a Transfer that exists is a valid one
    public Transfer {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(from, "from");
        Objects.requireNonNull(to, "to");
        if (cents <= 0) throw new IllegalArgumentException("amount must be positive: " + cents);
        if (from.equals(to)) throw new IllegalArgumentException("a transfer needs two different accounts: " + from);
    }
}
