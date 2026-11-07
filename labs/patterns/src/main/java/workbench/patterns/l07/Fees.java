package workbench.patterns.l07;

import java.util.Comparator;
import java.util.Map;

/**
 * Two refactors of {@link LegacyRouter#fee}, and a strategy for choosing a PSP.
 * Both refactors must give exactly the answers the legacy code gives, for every payment.
 */
public final class Fees {
    private Fees() {}

    /** One fee rule. A lambda is a complete strategy. */
    @FunctionalInterface
    public interface FeeStrategy {
        long fee(Payment p);
    }

    /** A PSP's offer for one payment: its fee and its 95th-percentile latency. */
    public record Quote(String psp, long feeMinor, long p95Millis) {}

    /** Refactor 1: one strategy per {@link Method}, in a new {@link java.util.EnumMap}. */
    public static Map<Method, FeeStrategy> strategies() {
        throw new UnsupportedOperationException("TODO: an EnumMap with one lambda per Method");
    }

    /** The fee, found by looking up the payment's method in {@link #strategies()}. */
    public static long feeByMap(Payment p) {
        throw new UnsupportedOperationException("TODO: look up the strategy and apply it");
    }

    /** Refactor 2: the fee as ONE switch expression over {@code p.method()}, with no default. */
    public static long feeBySwitch(Payment p) {
        throw new UnsupportedOperationException("TODO: a switch expression with a case per Method");
    }

    /**
     * The order in which the router tries PSPs: lowest fee first; on equal fees, lowest p95 latency;
     * on equal latency, PSP name in alphabetical order. Build it from Comparator.comparing.
     */
    public static Comparator<Quote> cheapestThenFastest() {
        throw new UnsupportedOperationException("TODO: Comparator.comparing(...).thenComparing(...)");
    }
}
