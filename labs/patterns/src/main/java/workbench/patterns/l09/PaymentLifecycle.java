package workbench.patterns.l09;

import java.util.List;

/**
 * A payment's lifecycle as data. States and events are records; {@link #transition} is a pure function
 * from (state, event) to the next state. The moves it allows:
 *
 * <pre>
 *   Created    + Authorize(code, amount &gt; 0)          -&gt; Authorized(id, code, amount)
 *   Created    + Decline(reason)                      -&gt; Failed(id, reason)
 *   Authorized + Capture()                            -&gt; Captured(id, amount)
 *   Authorized + Decline(reason)                      -&gt; Failed(id, reason)
 *   Captured   + Refund(r), with 0 &lt; r &lt;= captured    -&gt; Refunded(id, r)
 *   Refunded, Failed: terminal, nothing is allowed
 * </pre>
 *
 * Anything else throws {@link #illegal(PaymentState, PaymentEvent)}.
 */
public final class PaymentLifecycle {
    private PaymentLifecycle() {}

    public sealed interface PaymentState permits Created, Authorized, Captured, Refunded, Failed {}
    public record Created(String id) implements PaymentState {}
    public record Authorized(String id, String authCode, long amountMinor) implements PaymentState {}
    public record Captured(String id, long amountMinor) implements PaymentState {}
    public record Refunded(String id, long amountMinor) implements PaymentState {}
    public record Failed(String id, String reason) implements PaymentState {}

    public sealed interface PaymentEvent permits Authorize, Capture, Refund, Decline {}
    public record Authorize(String authCode, long amountMinor) implements PaymentEvent {}
    public record Capture() implements PaymentEvent {}
    public record Refund(long amountMinor) implements PaymentEvent {}
    public record Decline(String reason) implements PaymentEvent {}

    /**
     * The next state. Write it as a switch expression over the STATE with no default (a new state must
     * break the build), and a switch over the event inside each case. Use record patterns and guards.
     */
    public static PaymentState transition(PaymentState s, PaymentEvent e) {
        throw new UnsupportedOperationException("TODO: switch over the state, then over the event");
    }

    /** The exception for a move the table above does not allow. Given. */
    public static IllegalStateException illegal(PaymentState s, PaymentEvent e) {
        return new IllegalStateException(e.getClass().getSimpleName() + " not allowed in " + s.getClass().getSimpleName());
    }

    /** The current state of payment {@code id} after {@code events}, starting from Created. Given: a fold over transition. */
    public static PaymentState replay(String id, List<PaymentEvent> events) {
        PaymentState s = new Created(id);
        for (PaymentEvent e : events) {
            s = transition(s, e);
        }
        return s;
    }
}
