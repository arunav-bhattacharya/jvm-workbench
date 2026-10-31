package workbench.jmm.l03;

import java.util.concurrent.atomic.AtomicInteger;

public class PaymentSession {
    public enum Status { PENDING, AUTHORIZED, CAPTURED, VOIDED }

    private final long authorizedCents;

    // volatile: one writer, and the new value never depends on the old one. Readers just need to see it.
    private volatile Status status = Status.PENDING;

    // volatile: one writer, and volatile also makes the 64-bit long write atomic (no torn halves).
    private volatile long lastHeartbeatMillis;

    // atomic: many writers doing read-modify-write. volatile would still lose updates.
    private final AtomicInteger attempts = new AtomicInteger();

    // lock: two fields that must change together and a check before each change.
    // Neither volatile nor two separate atomics can keep the invariant.
    private final Object money = new Object();
    private long capturedCents;   // guarded by money
    private long refundedCents;   // guarded by money

    public PaymentSession(long authorizedCents) {
        this.authorizedCents = authorizedCents;
    }

    public void setStatus(Status s) {
        status = s;
    }

    public Status status() {
        return status;
    }

    public void awaitStatus(Status wanted) {
        while (status != wanted) {
            Thread.onSpinWait();
        }
    }

    public void heartbeat(long nowMillis) {
        lastHeartbeatMillis = nowMillis;
    }

    public long lastHeartbeatMillis() {
        return lastHeartbeatMillis;
    }

    public long awaitHeartbeatAfter(long afterMillis) {
        long seen;
        while ((seen = lastHeartbeatMillis) <= afterMillis) {
            Thread.onSpinWait();
        }
        return seen;
    }

    public void recordAttempt() {
        attempts.incrementAndGet();
    }

    public int attempts() {
        return attempts.get();
    }

    public boolean tryCapture(long cents) {
        synchronized (money) {   // check and update as one step, with refunds kept out
            if (capturedCents + cents > authorizedCents) return false;
            capturedCents += cents;
            return true;
        }
    }

    public boolean tryRefund(long cents) {
        synchronized (money) {   // reads capturedCents, so it needs the same lock
            if (refundedCents + cents > capturedCents) return false;
            refundedCents += cents;
            return true;
        }
    }

    public long capturedCents() {
        synchronized (money) {
            return capturedCents;
        }
    }

    public long refundedCents() {
        synchronized (money) {
            return refundedCents;
        }
    }
}
