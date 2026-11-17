package workbench.patterns.l04;

import java.math.BigDecimal;
import java.util.Map;

/** Helpers for talking to the old warehouse program. Given; you don't need to change them. */
public final class Units {
    private Units() {}

    private static final Map<String, String> ITEM_NUMBERS = Map.of(
            "FLOUR", "4711",
            "SUGAR", "4802",
            "TEA", "5150");

    /** 1250 grams is "1.250", 5 grams is "0.005", 30000 grams is "30.000": kilograms with three decimals. */
    public static String toKilos(long grams) {
        return BigDecimal.valueOf(grams, 3).toPlainString();
    }

    /** The warehouse's own number for one of our products: "FLOUR" is "4711". Unknown products throw. */
    public static String itemNumber(String product) {
        String n = ITEM_NUMBERS.get(product);
        if (n == null) throw new IllegalArgumentException("the warehouse has no number for " + product);
        return n;
    }
}
