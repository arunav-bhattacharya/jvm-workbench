package workbench.jmm.l04;

import java.util.Map;

// final class: no subclass can add mutable state or override the getters
public final class RateCard {
    // final fields: any thread that sees this RateCard sees these values as the constructor set them,
    // even if the RateCard itself was published through a data race
    private final String currency;
    private final Map<String, Long> feesByScheme;

    public RateCard(String currency, Map<String, Long> feesByScheme) {
        this.currency = currency;
        this.feesByScheme = Map.copyOf(feesByScheme);   // our own unmodifiable copy; the caller's map can't reach it
    }

    public String currency() {
        return currency;
    }

    public Map<String, Long> feesByScheme() {
        return feesByScheme;                            // safe to hand out: Map.copyOf is unmodifiable
    }

    public long feeFor(String scheme) {
        return feesByScheme.getOrDefault(scheme, 0L);
    }
}
