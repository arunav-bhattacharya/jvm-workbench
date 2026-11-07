package workbench.patterns.l09;

import java.util.List;
import java.util.function.Function;

/**
 * A fraud-screening pipeline as a Chain of Responsibility. Each {@link Check} either decides (returns
 * a verdict) or passes the request on (returns {@code next.proceed(r)}).
 */
public final class FraudChain {
    private FraudChain() {}

    /** What the pipeline looks at. */
    public record Request(String paymentId, long amountMinor, String cardCountry, String ipCountry) {}

    /** What it decides. */
    public sealed interface Verdict permits Approve, Review, Reject {}
    public record Approve() implements Verdict {}
    public record Review(String why) implements Verdict {}
    public record Reject(String why) implements Verdict {}

    /** The rest of the chain, as one check sees it. */
    @FunctionalInterface
    public interface Chain {
        Verdict proceed(Request r);
    }

    /** One link: decide now, or call {@code next.proceed(r)} to pass the request on. */
    @FunctionalInterface
    public interface Check {
        Verdict check(Request r, Chain next);
    }

    /**
     * Links {@code checks} in list order and ends in {@code terminal}. Calling {@code proceed} on the result
     * runs the first check; each check's {@code next} runs the one after it; after the last check, {@code next}
     * runs {@code terminal}. The result is immutable: it can serve many requests, on many threads.
     */
    public static Chain build(List<Check> checks, Function<Request, Verdict> terminal) {
        throw new UnsupportedOperationException("TODO: fold the checks into one Chain, last to first");
    }

    /** Rejects a payment above {@code maxMinor} with {@code Reject("over limit")}; otherwise passes it on. */
    public static Check amountLimit(long maxMinor) {
        throw new UnsupportedOperationException("TODO: a lambda (r, next) -> ...");
    }

    /** Sends a payment to {@code Review("country mismatch")} when card and IP countries differ; otherwise passes it on. */
    public static Check countryMismatch() {
        throw new UnsupportedOperationException("TODO: a lambda (r, next) -> ...");
    }
}
