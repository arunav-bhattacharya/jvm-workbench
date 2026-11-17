package workbench.patterns.l09;

import java.util.List;

/** A customer's return as a state machine: states and events are data, the rules are one pure function. */
public class ReturnStateDemo {
    sealed interface ReturnState permits Requested, Approved, Collected, BackOnShelf, Binned {}
    record Requested(String id, String item) implements ReturnState {}
    record Approved(String id, String item, String approver) implements ReturnState {}
    record Collected(String id, String item, String label) implements ReturnState {}
    record BackOnShelf(String id, String item) implements ReturnState {}
    record Binned(String id, String reason) implements ReturnState {}

    sealed interface ReturnEvent permits Approve, Collect, PutBack, Damaged {}
    record Approve(String approver) implements ReturnEvent {}
    record Collect(String label) implements ReturnEvent {}
    record PutBack() implements ReturnEvent {}
    record Damaged(String reason) implements ReturnEvent {}

    static ReturnState next(ReturnState s, ReturnEvent e) {
        return switch (s) {                                     // no default: a new state breaks the build
            case Requested(var id, var item) -> switch (e) {
                case Approve(var who) when !who.isBlank() -> new Approved(id, item, who);
                default -> throw illegal(s, e);
            };
            case Approved(var id, var item, var who) -> switch (e) {
                case Collect(var label) -> new Collected(id, item, label);
                default -> throw illegal(s, e);
            };
            case Collected(var id, var item, var label) -> switch (e) {
                case PutBack() -> new BackOnShelf(id, item);
                case Damaged(var reason) -> new Binned(id, reason);
                default -> throw illegal(s, e);
            };
            case BackOnShelf done -> throw illegal(s, e);       // final
            case Binned done -> throw illegal(s, e);            // final
        };
    }

    // a second switch over the same states: the label on the shop's screen
    static String label(ReturnState s) {
        return switch (s) {
            case Requested r -> "waiting for approval";
            case Approved a -> "approved by " + a.approver();
            case Collected c -> "collected, label " + c.label();
            case BackOnShelf b -> b.item() + " is back on the shelf";
            case Binned b -> "binned: " + b.reason();
        };
    }

    static IllegalStateException illegal(ReturnState s, ReturnEvent e) {
        return new IllegalStateException(e.getClass().getSimpleName() + " not allowed in " + s.getClass().getSimpleName());
    }

    public static void main(String[] args) {
        ReturnState s = new Requested("rt-31", "teapot");
        System.out.println(label(s));
        for (ReturnEvent e : List.of(new Approve("dana"), new Collect("RT-0091"), new PutBack())) {
            s = next(s, e);
            System.out.println(label(s));
        }
        try {
            next(new Requested("rt-32", "kettle"), new Collect("RT-0092"));
        } catch (IllegalStateException ex) {
            System.out.println("rejected: " + ex.getMessage());
        }
    }
}
