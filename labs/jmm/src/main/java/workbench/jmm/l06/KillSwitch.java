package workbench.jmm.l06;

/**
 * A one-way switch that stops new authorizations when a card issuer goes down. Any thread may call
 * {@link #trip}; request threads call {@link #isTripped()} on every authorization.
 *
 * <p>Keep the reason in the plain field below and reach it through a static final VarHandle that you
 * look up yourself (copy the pattern from SettlementSlot). {@code trip} must be atomic: exactly one
 * caller wins, and every thread then sees the winner's reason. No volatile field, no synchronized.
 */
public final class KillSwitch {
    private String reason;   // null until tripped

    /** Trips the switch. Returns true for the one caller that tripped it, false for every caller after that. */
    public boolean trip(String why) {
        throw new UnsupportedOperationException("TODO: compareAndSet the reason from null to why");
    }

    /** True once any thread has tripped the switch. */
    public boolean isTripped() {
        throw new UnsupportedOperationException("TODO: an acquire read of the reason");
    }

    /** The winning reason, or null if the switch has not been tripped. */
    public String reason() {
        throw new UnsupportedOperationException("TODO: an acquire read of the reason");
    }
}
