package workbench.concurrency.l13;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Tracks refunds against captured payments. The rule: the total refunded for a payment may never
 * exceed what was captured. Support agents and an automatic chargeback job refund at the same time.
 *
 * <p>This version is check-then-act on a {@link ConcurrentHashMap}: two refunds can both read the same
 * "already refunded" amount, both pass the check, and refund more than was captured. Make
 * {@link #refund} atomic per payment. Keep {@code writeAuditLine()}, but outside any lock.
 */
public class RefundLedger {
    private final Map<String, Long> captured;
    private final Map<String, Long> refunded = new ConcurrentHashMap<>();

    /** {@code captured}: payment id to captured amount in cents. */
    public RefundLedger(Map<String, Long> captured) {
        this.captured = Map.copyOf(captured);
    }

    /** Refunds {@code cents} if that keeps the total within the captured amount. Returns whether it did. */
    public boolean refund(String paymentId, long cents) {
        Long cap = captured.get(paymentId);
        if (cap == null || cents <= 0) return false;
        long already = refunded.getOrDefault(paymentId, 0L);    // read
        if (already + cents > cap) return false;                // check
        writeAuditLine();                                       // a slow step between check and act
        refunded.put(paymentId, already + cents);               // act
        return true;
    }

    /** Total refunded so far for {@code paymentId}. */
    public long refunded(String paymentId) {
        return refunded.getOrDefault(paymentId, 0L);
    }

    // stands in for writing an audit record; it widens the gap between check and act
    private static void writeAuditLine() {
        for (int i = 0; i < 200; i++) Thread.onSpinWait();
    }
}
