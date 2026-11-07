package workbench.concurrency.l13;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class RefundLedger {
    private final Map<String, Long> captured;
    private final Map<String, Long> refunded = new ConcurrentHashMap<>();

    public RefundLedger(Map<String, Long> captured) {
        this.captured = Map.copyOf(captured);
    }

    public boolean refund(String paymentId, long cents) {
        Long cap = captured.get(paymentId);
        if (cap == null || cents <= 0) return false;
        boolean[] approved = {false};
        // check and act inside ONE compute call: atomic for this payment, other payments are not blocked
        refunded.compute(paymentId, (id, already) -> {
            long done = already == null ? 0 : already;
            if (done + cents > cap) return already;             // over the captured amount: change nothing
            approved[0] = true;
            return done + cents;
        });
        if (approved[0]) writeAuditLine();                      // slow work after the update, outside the bin lock
        return approved[0];
        // a synchronized refund() would also be correct; it just makes every payment wait for every other
    }

    public long refunded(String paymentId) {
        return refunded.getOrDefault(paymentId, 0L);
    }

    private static void writeAuditLine() {
        for (int i = 0; i < 200; i++) Thread.onSpinWait();
    }
}
