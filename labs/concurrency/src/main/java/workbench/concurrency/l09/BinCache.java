package workbench.concurrency.l09;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/**
 * Caches the issuer for each card BIN (the first digits of a card number). The loader calls a
 * slow issuer-directory service, so it should run at most once per BIN.
 *
 * <p>This version is check-then-act on a {@link ConcurrentHashMap}: when eight requests for the
 * same new BIN arrive together, all eight see a miss and all eight call the loader.
 * Fix {@link #issuerFor} with one atomic map call, so the loader runs once per BIN.
 * If the loader throws, nothing is cached and the exception reaches the caller.
 */
public class BinCache {
    private final Map<String, String> issuers = new ConcurrentHashMap<>();
    private final Function<String, String> loader;

    public BinCache(Function<String, String> loader) {
        this.loader = loader;
    }

    /** The issuer for {@code bin}, loading it on the first request. */
    public String issuerFor(String bin) {
        String issuer = issuers.get(bin);       // check
        if (issuer == null) {
            issuer = loader.apply(bin);         // slow: other threads miss too while this runs
            issuers.put(bin, issuer);           // act
        }
        return issuer;
    }

    /** How many BINs are cached. */
    public int size() {
        return issuers.size();
    }
}
