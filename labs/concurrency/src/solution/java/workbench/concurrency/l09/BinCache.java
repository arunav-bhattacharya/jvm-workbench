package workbench.concurrency.l09;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

public class BinCache {
    private final Map<String, String> issuers = new ConcurrentHashMap<>();
    private final Function<String, String> loader;

    public BinCache(Function<String, String> loader) {
        this.loader = loader;
    }

    public String issuerFor(String bin) {
        // one atomic call: the loader runs at most once per BIN, and other callers for the
        // same BIN wait for its result. If the loader throws, no mapping is stored.
        return issuers.computeIfAbsent(bin, loader);
    }

    public int size() {
        return issuers.size();
    }
}
