package workbench.modernjava.l01;

import java.util.List;

/**
 * A refund of part of a captured payment, with the reasons the support agent picked.
 *
 * <p>TODO 3: add a compact canonical constructor that
 * <ul>
 *   <li>rejects a null {@code paymentId}, {@code amount} or {@code reasons} with a {@link NullPointerException},</li>
 *   <li>rejects a blank {@code paymentId} with an {@link IllegalArgumentException},</li>
 *   <li>replaces {@code reasons} with an unmodifiable copy, so later changes to the caller's
 *       list don't show up in the record,</li>
 *   <li>rejects an empty list of reasons with an {@link IllegalArgumentException}.</li>
 * </ul>
 */
public record Refund(String paymentId, Money amount, List<String> reasons) {

    /**
     * TODO 4: returns a refund like this one but with {@code newAmount}.
     * The new value must pass the same checks as any other refund.
     */
    public Refund withAmount(Money newAmount) {
        throw new UnsupportedOperationException("TODO: withAmount");
    }
}
