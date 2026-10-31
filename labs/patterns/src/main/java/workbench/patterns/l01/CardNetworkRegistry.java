package workbench.patterns.l01;

import java.util.Map;
import java.util.function.Supplier;

/**
 * Sandbox base URLs for each card network ("VISA", "MASTERCARD", ...), loaded once, on first use.
 *
 * <p>Loading is slow (it reads files and calls a config service), so the registry waits until
 * someone asks. The loader comes in through the constructor, so tests can pass a fake one.
 *
 * <p>This version is lazy but not thread-safe: when several request threads do the first lookup
 * together, each of them runs the loader. Fix {@link #table()} so the loader runs at most once per
 * registry, even under contention, and every caller gets the same map. A failed load must not be
 * cached: the next call tries again.
 */
public final class CardNetworkRegistry {
    private final Supplier<Map<String, String>> loader;
    private Map<String, String> table;   // null until the first successful load

    public CardNetworkRegistry(Supplier<Map<String, String>> loader) {
        this.loader = loader;
    }

    /** The whole table, loading it on the first call. Always the same instance after that. */
    public Map<String, String> table() {
        if (table == null) {                       // check
            table = Map.copyOf(loader.get());      // act: two threads can both get here
        }
        return table;
    }

    /** The sandbox URL for {@code network}. Throws IllegalArgumentException for an unknown network. */
    public String sandboxUrl(String network) {
        String url = table().get(network);
        if (url == null) throw new IllegalArgumentException("unknown card network: " + network);
        return url;
    }

    /** True once the table has been loaded. Never triggers a load. */
    public boolean isLoaded() {
        return table != null;
    }
}
