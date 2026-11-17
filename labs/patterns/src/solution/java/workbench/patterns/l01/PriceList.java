package workbench.patterns.l01;

import java.util.Map;
import java.util.function.Supplier;

public final class PriceList {
    private final Supplier<Map<String, Long>> loader;
    private final Object lock = new Object();
    // volatile: the write below publishes the fully built map to every thread that reads it later
    private volatile Map<String, Long> prices;

    public PriceList(Supplier<Map<String, Long>> loader) {
        this.loader = loader;
    }

    public Map<String, Long> prices() {
        Map<String, Long> p = prices;                // 1. fast path: one volatile read, no lock
        if (p == null) {
            synchronized (lock) {                    // 2. slow path: one thread at a time
                p = prices;                          // 3. re-check: another thread may have loaded it
                if (p == null) {
                    p = Map.copyOf(loader.get());    // 4. if this throws, prices stays null and the next call retries
                    prices = p;                      // 5. publish
                }
            }
        }
        return p;
    }

    public long priceOf(String product) {
        Long cents = prices().get(product);
        if (cents == null) throw new IllegalArgumentException("unknown product: " + product);
        return cents;
    }

    public boolean isLoaded() {
        return prices != null;
    }
}
