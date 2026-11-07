package workbench.concurrency.l11;

import java.math.BigDecimal;
import java.util.List;

/**
 * A signed FX quote that many request threads read at once, with no locks.
 * That is only safe if nobody can change it after it is built.
 *
 * <p>A record's fields are final, but this one is only shallowly immutable: it keeps the caller's
 * {@code List} and {@code byte[]}, and hands its own array out to anyone who asks.
 * Make it deeply immutable:
 * <ul>
 *   <li>copy {@code tiers} into an unmodifiable list in a compact constructor;</li>
 *   <li>copy {@code signature} in the constructor, and return a copy from {@link #signature()}.</li>
 * </ul>
 */
public record FxQuote(String pair, List<Tier> tiers, byte[] signature) {

    /** Up to {@code upToCents}, convert at {@code rate}. */
    public record Tier(long upToCents, BigDecimal rate) {}
}
