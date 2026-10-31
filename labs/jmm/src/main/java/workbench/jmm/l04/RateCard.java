package workbench.jmm.l04;

import java.util.Map;

/**
 * Card-scheme fees for one currency, e.g. VISA -> 120 cents. Request threads share one RateCard.
 *
 * <p>Make it immutable, so it is safe to share even through a data race: a final class, final fields,
 * a defensive copy of the map in the constructor, and a getter that can't be used to change it.
 * Keep the public constructor and methods as they are.
 */
public class RateCard {
    private String currency;
    private Map<String, Long> feesByScheme;

    public RateCard(String currency, Map<String, Long> feesByScheme) {
        this.currency = currency;
        this.feesByScheme = feesByScheme;   // keeps the caller's map: they can still change it
    }

    public String currency() {
        return currency;
    }

    public Map<String, Long> feesByScheme() {
        return feesByScheme;                // hands out the internal map: anyone can change it
    }

    public long feeFor(String scheme) {
        return feesByScheme.getOrDefault(scheme, 0L);
    }
}
