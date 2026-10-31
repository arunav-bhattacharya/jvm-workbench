package workbench.patterns.l01;

import java.util.Map;
import java.util.function.Supplier;

public final class CardNetworkRegistry {
    private final Supplier<Map<String, String>> loader;
    private final Object lock = new Object();
    // volatile: the write below publishes the fully built map to every thread that reads it later
    private volatile Map<String, String> table;

    public CardNetworkRegistry(Supplier<Map<String, String>> loader) {
        this.loader = loader;
    }

    public Map<String, String> table() {
        Map<String, String> t = table;               // 1. fast path: one volatile read, no lock
        if (t == null) {
            synchronized (lock) {                    // 2. slow path: one thread at a time
                t = table;                           // 3. re-check: another thread may have loaded it
                if (t == null) {
                    t = Map.copyOf(loader.get());    // 4. if this throws, table stays null and the next call retries
                    table = t;                       // 5. publish
                }
            }
        }
        return t;
    }

    public String sandboxUrl(String network) {
        String url = table().get(network);
        if (url == null) throw new IllegalArgumentException("unknown card network: " + network);
        return url;
    }

    public boolean isLoaded() {
        return table != null;
    }
}
