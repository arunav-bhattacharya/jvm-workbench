package workbench.patterns.l07;

import java.util.Comparator;
import java.util.EnumMap;
import java.util.Map;

public final class Fees {
    private Fees() {}

    @FunctionalInterface
    public interface FeeStrategy {
        long fee(Payment p);
    }

    public record Quote(String psp, long feeMinor, long p95Millis) {}

    public static Map<Method, FeeStrategy> strategies() {
        // an open set: a map can be filled from config or plug-ins. A missing entry is a RUNTIME failure.
        Map<Method, FeeStrategy> m = new EnumMap<>(Method.class);
        m.put(Method.CARD, p -> 30 + p.amountMinor() * 290 / 10_000
                + (p.country().equals("DE") ? 0 : p.amountMinor() * 100 / 10_000));
        m.put(Method.SEPA, p -> 25);
        m.put(Method.WALLET, p -> p.amountMinor() * 150 / 10_000);
        return m;
    }

    public static long feeByMap(Payment p) {
        return strategies().get(p.method()).fee(p);
    }

    public static long feeBySwitch(Payment p) {
        // a closed set: no default, so a new Method is a COMPILE error here
        return switch (p.method()) {
            case CARD -> 30 + p.amountMinor() * 290 / 10_000
                    + (p.country().equals("DE") ? 0 : p.amountMinor() * 100 / 10_000);
            case SEPA -> 25;
            case WALLET -> p.amountMinor() * 150 / 10_000;
        };
    }

    public static Comparator<Quote> cheapestThenFastest() {
        // three strategies composed into one: the JDK's Comparator is Strategy with combinators
        return Comparator.comparingLong(Quote::feeMinor)
                .thenComparingLong(Quote::p95Millis)
                .thenComparing(Quote::psp);
    }
}
