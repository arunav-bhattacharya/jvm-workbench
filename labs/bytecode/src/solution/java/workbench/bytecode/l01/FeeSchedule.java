package workbench.bytecode.l01;

import java.util.Map;

public final class FeeSchedule {
    private static final Map<String, Integer> BPS_BY_COUNTRY = Map.of("DE", 290, "FR", 310);
    // <clinit> runs the static initializers in source order, so every field the constructor
    // reads must be assigned ABOVE the line that calls the constructor
    private static final int DEFAULT_BPS = Integer.parseInt(System.getProperty("fees.default.bps", "350"));
    private static final String CURRENCY = "EUR";

    // moved below the fields it needs
    public static final FeeSchedule INSTANCE = new FeeSchedule();

    private final int fallbackBps;
    private final String currency;

    private FeeSchedule() {
        fallbackBps = DEFAULT_BPS;
        currency = CURRENCY;
    }

    public int bpsFor(String country) {
        return BPS_BY_COUNTRY.getOrDefault(country, fallbackBps);
    }

    public String currency() {
        return currency;
    }
}
