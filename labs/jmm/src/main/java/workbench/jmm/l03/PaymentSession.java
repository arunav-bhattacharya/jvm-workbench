package workbench.jmm.l03;

/**
 * One card payment, shared by several threads. Right now no field is protected at all.
 *
 * <p>Go field by field. Read who writes it and who reads it, then choose the lightest tool that is
 * correct: {@code volatile}, a class from {@code java.util.concurrent.atomic}, or a lock.
 * Don't change any public method signature. Add a one-line comment next to each field saying why.
 */
public class PaymentSession {
    public enum Status { PENDING, AUTHORIZED, CAPTURED, VOIDED }

    private final long authorizedCents;

    // Written only by the issuer callback thread. Read by request threads and by awaitStatus().
    private Status status = Status.PENDING;

    // Written only by the heartbeat thread (epoch millis). Read by the watchdog thread.
    private long lastHeartbeatMillis;

    // Incremented by every retry thread. Read by the metrics thread.
    private int attempts;

    // Changed by capture threads and refund threads.
    // Invariant: 0 <= refundedCents <= capturedCents <= authorizedCents.
    private long capturedCents;
    private long refundedCents;

    public PaymentSession(long authorizedCents) {
        this.authorizedCents = authorizedCents;
    }

    // ---- status: one writer, many readers ----

    public void setStatus(Status s) {
        status = s;
    }

    public Status status() {
        return status;
    }

    /** Spins until the status equals {@code wanted}. */
    public void awaitStatus(Status wanted) {
        while (status != wanted) {
            // wait for the issuer callback
        }
    }

    // ---- heartbeat: one writer, one reader ----

    public void heartbeat(long nowMillis) {
        lastHeartbeatMillis = nowMillis;
    }

    public long lastHeartbeatMillis() {
        return lastHeartbeatMillis;
    }

    /** Spins until a heartbeat later than {@code afterMillis} arrives, then returns it. */
    public long awaitHeartbeatAfter(long afterMillis) {
        long seen;
        while ((seen = lastHeartbeatMillis) <= afterMillis) {
            // wait for the heartbeat thread
        }
        return seen;
    }

    // ---- attempts: many writers ----

    public void recordAttempt() {
        attempts++;
    }

    public int attempts() {
        return attempts;
    }

    // ---- money: many writers, two fields, one invariant ----

    /** Captures {@code cents} if the total captured stays within the authorization. */
    public boolean tryCapture(long cents) {
        if (capturedCents + cents > authorizedCents) return false;
        capturedCents += cents;
        return true;
    }

    /** Refunds {@code cents} if the total refunded stays within what was captured. */
    public boolean tryRefund(long cents) {
        if (refundedCents + cents > capturedCents) return false;
        refundedCents += cents;
        return true;
    }

    public long capturedCents() {
        return capturedCents;
    }

    public long refundedCents() {
        return refundedCents;
    }
}
