package workbench.patterns.l07;

import java.util.EnumMap;
import java.util.Map;

/** The same delivery prices as a map of strategies and as a switch. Add a way to deliver and watch which one tells you. */
public class RouterDemo {
    enum Way { BIKE, VAN, PICKUP }
    record Job(Way way, int grams) {}
    interface PriceStrategy { long priceCents(Job j); }

    // open set: one lambda per way, in a map that settings or plug-ins could fill
    static final Map<Way, PriceStrategy> STRATEGIES = new EnumMap<>(Map.of(
            Way.BIKE, j -> 200 + j.grams() * 30 / 1_000,
            Way.VAN, j -> 450,
            Way.PICKUP, j -> 0));

    // closed set: one switch, checked by the compiler
    static long priceSwitch(Job j) {
        return switch (j.way()) {
            case BIKE -> 200 + j.grams() * 30 / 1_000;
            case VAN -> 450;
            case PICKUP -> 0;
        };
    }

    public static void main(String[] args) {
        for (Way w : Way.values()) {
            Job j = new Job(w, 2_500);
            System.out.printf("%-7s switch=%d", w, priceSwitch(j));
            System.out.printf("  map=%d%n", STRATEGIES.get(w).priceCents(j));
        }
    }
}
