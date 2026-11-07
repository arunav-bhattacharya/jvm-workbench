package workbench.modernjava.l01;

import java.util.List;
import java.util.Objects;

public record Refund(String paymentId, Money amount, List<String> reasons) {

    public Refund {
        Objects.requireNonNull(paymentId, "paymentId");
        Objects.requireNonNull(amount, "amount");
        if (paymentId.isBlank()) {
            throw new IllegalArgumentException("blank paymentId");
        }
        // a record is only as immutable as its components: copy the caller's list.
        // List.copyOf also throws NullPointerException for a null list or a null element.
        reasons = List.copyOf(reasons);
        if (reasons.isEmpty()) {
            throw new IllegalArgumentException("a refund needs at least one reason");
        }
    }

    // a hand-written wither: it calls the canonical constructor, so the new value is validated too
    public Refund withAmount(Money newAmount) {
        return new Refund(paymentId, newAmount, reasons);
    }
}
