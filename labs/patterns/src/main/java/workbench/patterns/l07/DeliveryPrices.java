package workbench.patterns.l07;

import java.util.Comparator;
import java.util.Map;

/**
 * Two refactors of {@link LegacyPricer#priceCents}, and a strategy for choosing a courier.
 * Both refactors must give exactly the answers the legacy code gives, for every parcel.
 */
public final class DeliveryPrices {
    private DeliveryPrices() {}

    /** One pricing rule. A lambda is a complete strategy. */
    @FunctionalInterface
    public interface PriceStrategy {
        long priceCents(Parcel p);
    }

    /** A courier company's offer for one parcel: its price and how many minutes it takes. */
    public record Quote(String courier, long priceCents, long minutes) {}

    /** Refactor 1: one strategy per {@link DeliveryMethod}, in a new {@link java.util.EnumMap}. */
    public static Map<DeliveryMethod, PriceStrategy> strategies() {
        throw new UnsupportedOperationException("TODO: an EnumMap with one lambda per DeliveryMethod");
    }

    /** The price, found by looking up the parcel's method in {@link #strategies()}. */
    public static long priceByMap(Parcel p) {
        throw new UnsupportedOperationException("TODO: look up the strategy and apply it");
    }

    /** Refactor 2: the price as ONE switch expression over {@code p.method()}, with no default. */
    public static long priceBySwitch(Parcel p) {
        throw new UnsupportedOperationException("TODO: a switch expression with a case per DeliveryMethod");
    }

    /**
     * The order in which the shop asks couriers: lowest price first; on equal prices, fewest minutes;
     * on equal minutes, courier name in alphabetical order. Build it from Comparator.comparing.
     */
    public static Comparator<Quote> cheapestThenFastest() {
        throw new UnsupportedOperationException("TODO: Comparator.comparing(...).thenComparing(...)");
    }
}
