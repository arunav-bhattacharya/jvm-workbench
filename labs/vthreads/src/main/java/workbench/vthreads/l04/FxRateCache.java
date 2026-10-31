package workbench.vthreads.l04;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

/**
 * Caches FX rates ("EURUSD" -> 1.0842). A miss calls the rates service, which takes about 100 ms.
 * Many virtual threads call {@link #rate} at once, and each pair must be loaded only once.
 *
 * <p>This version holds a monitor ({@code synchronized}) during the slow call. On JDK 21 to 23 that
 * pins the virtual thread to its carrier for the whole call, and every other caller that blocks on
 * the monitor pins its carrier too. Replace the monitor with a {@link java.util.concurrent.locks.ReentrantLock},
 * keeping the "load each pair once" behavior.
 */
public class FxRateCache {
    private final Map<String, BigDecimal> rates = new HashMap<>();
    private final Function<String, BigDecimal> ratesService;

    public FxRateCache(Function<String, BigDecimal> ratesService) {
        this.ratesService = ratesService;
    }

    /** The rate for {@code pair}, loading it from the rates service on the first request. */
    public synchronized BigDecimal rate(String pair) {
        BigDecimal r = rates.get(pair);
        if (r == null) {
            r = ratesService.apply(pair);   // ~100 ms blocking HTTP call, made while holding the monitor
            rates.put(pair, r);
        }
        return r;
    }

    /** How many pairs are cached. */
    public synchronized int size() {
        return rates.size();
    }
}
