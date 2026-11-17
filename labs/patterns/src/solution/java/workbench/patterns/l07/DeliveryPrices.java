package workbench.patterns.l07;

import java.util.Comparator;
import java.util.EnumMap;
import java.util.Map;

public final class DeliveryPrices {
    private DeliveryPrices() {}

    @FunctionalInterface
    public interface PriceStrategy {
        long priceCents(Parcel p);
    }

    public record Quote(String courier, long priceCents, long minutes) {}

    public static Map<DeliveryMethod, PriceStrategy> strategies() {
        // an open set: a map can be filled from settings or plug-ins. A missing entry is a RUNTIME failure.
        Map<DeliveryMethod, PriceStrategy> m = new EnumMap<>(DeliveryMethod.class);
        m.put(DeliveryMethod.BIKE, p -> 200 + p.grams() * 30 / 1_000
                + (p.district().equals("Old Town") ? 0 : p.grams() * 10 / 1_000));   // two divisions, as the legacy code does
        m.put(DeliveryMethod.VAN, p -> 450);
        m.put(DeliveryMethod.PICKUP, p -> 0);
        return m;
    }

    public static long priceByMap(Parcel p) {
        return strategies().get(p.method()).priceCents(p);
    }

    public static long priceBySwitch(Parcel p) {
        // a closed set: no default, so a new DeliveryMethod is a COMPILE error here
        return switch (p.method()) {
            case BIKE -> 200 + p.grams() * 30 / 1_000
                    + (p.district().equals("Old Town") ? 0 : p.grams() * 10 / 1_000);
            case VAN -> 450;
            case PICKUP -> 0;
        };
    }

    public static Comparator<Quote> cheapestThenFastest() {
        // three strategies composed into one: the JDK's Comparator is Strategy with combinators
        return Comparator.comparingLong(Quote::priceCents)
                .thenComparingLong(Quote::minutes)
                .thenComparing(Quote::courier);
    }
}
