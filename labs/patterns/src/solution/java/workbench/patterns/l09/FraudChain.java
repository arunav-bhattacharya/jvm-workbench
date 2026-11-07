package workbench.patterns.l09;

import java.util.List;
import java.util.function.Function;

public final class FraudChain {
    private FraudChain() {}

    public record Request(String paymentId, long amountMinor, String cardCountry, String ipCountry) {}

    public sealed interface Verdict permits Approve, Review, Reject {}
    public record Approve() implements Verdict {}
    public record Review(String why) implements Verdict {}
    public record Reject(String why) implements Verdict {}

    @FunctionalInterface
    public interface Chain {
        Verdict proceed(Request r);
    }

    @FunctionalInterface
    public interface Check {
        Verdict check(Request r, Chain next);
    }

    public static Chain build(List<Check> checks, Function<Request, Verdict> terminal) {
        List<Check> copy = List.copyOf(checks);              // later edits to the caller's list can't change the chain
        Chain next = terminal::apply;                          // the end of the chain
        for (int i = copy.size() - 1; i >= 0; i--) {           // fold from the last check to the first
            Check check = copy.get(i);
            Chain rest = next;
            next = r -> check.check(r, rest);                  // each link knows only the rest of the chain
        }
        return next;
    }

    public static Check amountLimit(long maxMinor) {
        return (r, next) -> r.amountMinor() > maxMinor ? new Reject("over limit") : next.proceed(r);
    }

    public static Check countryMismatch() {
        return (r, next) -> r.cardCountry().equals(r.ipCountry()) ? next.proceed(r) : new Review("country mismatch");
    }
}
