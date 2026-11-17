package workbench.patterns.l01;

import java.util.Map;
import java.util.function.Supplier;

/**
 * The corner shop's price list: the price in cents of every product, by product code ("BREAD",
 * "MILK", ...), loaded once, on first use.
 *
 * <p>Loading is slow (it reads the supplier's price file), so the price list waits until someone
 * asks. The loader comes in through the constructor, so tests can pass a fake one.
 *
 * <p>This version is lazy but not thread-safe: when several threads look up a price for the first
 * time together, each of them runs the loader. Fix {@link #prices()} so the loader runs at most once
 * per price list, even under contention, and every caller gets the same map. A failed load must not
 * be cached: the next call tries again.
 */
public final class PriceList {
    private final Supplier<Map<String, Long>> loader;
    private Map<String, Long> prices;   // null until the first successful load

    public PriceList(Supplier<Map<String, Long>> loader) {
        this.loader = loader;
    }

    /** Every price, loading them on the first call. Always the same map instance after that. */
    public Map<String, Long> prices() {
        if (prices == null) {                       // check
            prices = Map.copyOf(loader.get());      // act: two threads can both get here
        }
        return prices;
    }

    /** The price of {@code product} in cents. Throws IllegalArgumentException for an unknown product. */
    public long priceOf(String product) {
        Long cents = prices().get(product);
        if (cents == null) throw new IllegalArgumentException("unknown product: " + product);
        return cents;
    }

    /** True once the prices have been loaded. Never triggers a load. */
    public boolean isLoaded() {
        return prices != null;
    }
}
