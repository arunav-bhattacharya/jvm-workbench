package workbench.startup.l03;

/**
 * An event on the payments topic. {@link EventDecoder} creates and reads it only through
 * reflection, the way a JSON library does. Don't change this class.
 */
public final class PaymentAuthorized {
    private final String paymentId;
    private final String currency;
    private final long amountMinor;

    public PaymentAuthorized(String paymentId, String currency, long amountMinor) {
        this.paymentId = paymentId;
        this.currency = currency;
        this.amountMinor = amountMinor;
    }

    public String paymentId() {
        return paymentId;
    }

    public String currency() {
        return currency;
    }

    public long amountMinor() {
        return amountMinor;
    }

    /** Nobody calls this reflectively, so it needs no metadata. */
    public String summary() {
        return paymentId + " " + amountMinor + " " + currency;
    }
}
