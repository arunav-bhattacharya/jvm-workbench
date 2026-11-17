package workbench.patterns.l09;

import java.util.List;
import java.util.function.Function;

public final class ComplaintDesk {
    private ComplaintDesk() {}

    public record Complaint(String orderNo, String about, int worthCents) {}

    public record Reply(String from, String says) {}

    @FunctionalInterface
    public interface Chain {
        Reply passOn(Complaint c);
    }

    @FunctionalInterface
    public interface Handler {
        Reply handle(Complaint c, Chain next);
    }

    public static Chain build(List<Handler> handlers, Function<Complaint, Reply> lastStop) {
        List<Handler> copy = List.copyOf(handlers);              // later edits to the caller's list can't change the chain
        Chain next = lastStop::apply;                            // the end of the chain
        for (int i = copy.size() - 1; i >= 0; i--) {             // fold from the last handler to the first
            Handler handler = copy.get(i);
            Chain rest = next;
            next = c -> handler.handle(c, rest);                 // each link knows only the rest of the chain
        }
        return next;
    }

    public static Handler upTo(String who, int maxCents) {
        return (c, next) -> c.worthCents() <= maxCents ? new Reply(who, "sorted") : next.passOn(c);
    }

    public static Handler lateDelivery() {
        return (c, next) -> c.about().equals("late") ? new Reply("courier desk", "passed to the courier") : next.passOn(c);
    }
}
