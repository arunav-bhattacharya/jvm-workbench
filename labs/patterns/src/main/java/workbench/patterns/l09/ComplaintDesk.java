package workbench.patterns.l09;

import java.util.List;
import java.util.function.Function;

/**
 * The shop's complaint desk as a Chain of Responsibility. A complaint passes along a list of handlers,
 * such as the shop assistant and then the manager. Each {@link Handler} either answers it (returns a
 * reply) or passes it on (returns {@code next.passOn(c)}). Whatever nobody answers reaches the last stop,
 * head office.
 */
public final class ComplaintDesk {
    private ComplaintDesk() {}

    /** What a customer complains about, and what putting it right is worth, in cents (250 means 2.50). */
    public record Complaint(String orderNo, String about, int worthCents) {}

    /** The answer, and who gave it. */
    public record Reply(String from, String says) {}

    /** The rest of the chain, as one handler sees it. */
    @FunctionalInterface
    public interface Chain {
        Reply passOn(Complaint c);
    }

    /** One link: answer now, or call {@code next.passOn(c)} to pass the complaint on. */
    @FunctionalInterface
    public interface Handler {
        Reply handle(Complaint c, Chain next);
    }

    /**
     * Links {@code handlers} in list order and ends in {@code lastStop}. Calling {@code passOn} on the result
     * runs the first handler; each handler's {@code next} runs the one after it; after the last handler,
     * {@code next} runs {@code lastStop}. The result is immutable: it can serve many complaints, on many threads.
     */
    public static Chain build(List<Handler> handlers, Function<Complaint, Reply> lastStop) {
        throw new UnsupportedOperationException("TODO: fold the handlers into one Chain, last to first");
    }

    /**
     * A person who sorts out any complaint worth at most {@code maxCents}, answering
     * {@code Reply(who, "sorted")}, and passes bigger ones on.
     */
    public static Handler upTo(String who, int maxCents) {
        throw new UnsupportedOperationException("TODO: a lambda (c, next) -> ...");
    }

    /**
     * Sends a complaint about a late delivery ({@code about} equal to "late") to
     * {@code Reply("courier desk", "passed to the courier")}, and passes anything else on.
     */
    public static Handler lateDelivery() {
        throw new UnsupportedOperationException("TODO: a lambda (c, next) -> ...");
    }
}
