package workbench.patterns.l09;

import java.util.List;

/** A merchant payout as a state machine: states and events are data, the rules are one pure function. */
public class PayoutStateDemo {
    sealed interface PayoutState permits Requested, Approved, Sent, Settled, Returned {}
    record Requested(String id, long amountMinor) implements PayoutState {}
    record Approved(String id, long amountMinor, String approver) implements PayoutState {}
    record Sent(String id, long amountMinor, String bankRef) implements PayoutState {}
    record Settled(String id, long amountMinor) implements PayoutState {}
    record Returned(String id, String reason) implements PayoutState {}

    sealed interface PayoutEvent permits Approve, Send, Confirm, BankReturn {}
    record Approve(String approver) implements PayoutEvent {}
    record Send(String bankRef) implements PayoutEvent {}
    record Confirm() implements PayoutEvent {}
    record BankReturn(String reason) implements PayoutEvent {}

    static PayoutState next(PayoutState s, PayoutEvent e) {
        return switch (s) {                                     // no default: a new state breaks the build
            case Requested(var id, var amt) -> switch (e) {
                case Approve(var who) when !who.isBlank() -> new Approved(id, amt, who);
                default -> throw illegal(s, e);
            };
            case Approved(var id, var amt, var who) -> switch (e) {
                case Send(var ref) -> new Sent(id, amt, ref);
                default -> throw illegal(s, e);
            };
            case Sent(var id, var amt, var ref) -> switch (e) {
                case Confirm() -> new Settled(id, amt);
                case BankReturn(var reason) -> new Returned(id, reason);
                default -> throw illegal(s, e);
            };
            case Settled done -> throw illegal(s, e);           // terminal
            case Returned done -> throw illegal(s, e);          // terminal
        };
    }

    // a second switch over the same states: the API's status label
    static String label(PayoutState s) {
        return switch (s) {
            case Requested r -> "pending approval";
            case Approved a -> "approved by " + a.approver();
            case Sent t -> "sent, bank ref " + t.bankRef();
            case Settled d -> "settled";
            case Returned r -> "returned: " + r.reason();
        };
    }

    static IllegalStateException illegal(PayoutState s, PayoutEvent e) {
        return new IllegalStateException(e.getClass().getSimpleName() + " not allowed in " + s.getClass().getSimpleName());
    }

    public static void main(String[] args) {
        PayoutState s = new Requested("po-31", 125_000);
        System.out.println(label(s));
        for (PayoutEvent e : List.of(new Approve("dana"), new Send("DE-REF-0091"), new Confirm())) {
            s = next(s, e);
            System.out.println(label(s));
        }
        try {
            next(new Requested("po-32", 900), new Send("DE-REF-0092"));
        } catch (IllegalStateException ex) {
            System.out.println("rejected: " + ex.getMessage());
        }
    }
}
