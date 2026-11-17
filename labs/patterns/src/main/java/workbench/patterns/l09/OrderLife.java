package workbench.patterns.l09;

import java.util.List;

/**
 * An order's life at the corner shop, as data. States and events are records; {@link #transition} is a
 * pure function from (state, event) to the next state. The moves it allows:
 *
 * <pre>
 *   Placed         + Pack(parcels &gt; 0)            -&gt; Packed(orderNo, parcels)
 *   Placed         + Cancel(reason)                -&gt; Cancelled(orderNo, reason)
 *   Packed         + Ship(courier)                 -&gt; OutForDelivery(orderNo, parcels, courier)
 *   Packed         + Cancel(reason)                -&gt; Cancelled(orderNo, reason)
 *   OutForDelivery + Deliver(signedBy), not blank  -&gt; Delivered(orderNo, signedBy)
 *   Delivered, Cancelled: final, nothing is allowed
 * </pre>
 *
 * Anything else throws {@link #illegal(OrderState, OrderEvent)}. Note that an order that is out for
 * delivery can't be cancelled any more: the parcel is already on the bike or in the van.
 */
public final class OrderLife {
    private OrderLife() {}

    public sealed interface OrderState permits Placed, Packed, OutForDelivery, Delivered, Cancelled {}
    public record Placed(String orderNo) implements OrderState {}
    public record Packed(String orderNo, int parcels) implements OrderState {}
    public record OutForDelivery(String orderNo, int parcels, String courier) implements OrderState {}
    public record Delivered(String orderNo, String signedBy) implements OrderState {}
    public record Cancelled(String orderNo, String reason) implements OrderState {}

    public sealed interface OrderEvent permits Pack, Ship, Deliver, Cancel {}
    public record Pack(int parcels) implements OrderEvent {}
    public record Ship(String courier) implements OrderEvent {}
    public record Deliver(String signedBy) implements OrderEvent {}
    public record Cancel(String reason) implements OrderEvent {}

    /**
     * The next state. Write it as a switch expression over the STATE with no default (a new state must
     * break the build), and a switch over the event inside each case. Use record patterns and guards.
     */
    public static OrderState transition(OrderState s, OrderEvent e) {
        throw new UnsupportedOperationException("TODO: switch over the state, then over the event");
    }

    /** The exception for a move the table above does not allow. Given. */
    public static IllegalStateException illegal(OrderState s, OrderEvent e) {
        return new IllegalStateException(e.getClass().getSimpleName() + " not allowed in " + s.getClass().getSimpleName());
    }

    /** The state of order {@code orderNo} after {@code events}, starting from Placed. Given: a fold over transition. */
    public static OrderState replay(String orderNo, List<OrderEvent> events) {
        OrderState s = new Placed(orderNo);
        for (OrderEvent e : events) {
            s = transition(s, e);
        }
        return s;
    }
}
