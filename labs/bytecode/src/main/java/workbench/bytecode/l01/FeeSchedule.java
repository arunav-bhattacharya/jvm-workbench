package workbench.bytecode.l01;

import java.util.Map;

/**
 * Card fees in basis points (1 bps = 0.01%), one shared instance.
 *
 * <p>A payment from an unknown country should pay the default fee, 350 bps. It pays 0, and
 * nothing throws. Read the static initializer from top to bottom, the way the JVM runs it,
 * and fix the class without changing any number.
 */
public final class FeeSchedule {
    private static final Map<String, Integer> BPS_BY_COUNTRY = Map.of("DE", 290, "FR", 310);

    public static final FeeSchedule INSTANCE = new FeeSchedule();

    // not a compile-time constant (it calls a method), so it is assigned when <clinit> reaches this line
    private static final int DEFAULT_BPS = Integer.parseInt(System.getProperty("fees.default.bps", "350"));
    // a compile-time constant: javac copies "EUR" into every place that reads it
    private static final String CURRENCY = "EUR";

    private final int fallbackBps;
    private final String currency;

    private FeeSchedule() {
        fallbackBps = DEFAULT_BPS;
        currency = CURRENCY;
    }

    /** Fee in basis points for a card issued in {@code country}. */
    public int bpsFor(String country) {
        return BPS_BY_COUNTRY.getOrDefault(country, fallbackBps);
    }

    public String currency() {
        return currency;
    }
}
