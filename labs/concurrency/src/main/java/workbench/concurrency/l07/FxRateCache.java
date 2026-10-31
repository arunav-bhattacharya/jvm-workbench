package workbench.concurrency.l07;

import java.math.BigDecimal;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.function.Function;

/**
 * A read-mostly cache of FX rates. Thousands of reads per second, a refresh every few seconds.
 * Reads share a read lock; writes take the write lock.
 *
 * <p>Two bugs to fix:
 * <ol>
 *   <li>{@link #rate} hangs the first time a pair is missing: it tries to take the write lock while
 *       still holding the read lock. Release the read lock first, then take the write lock and
 *       re-check before loading, so the loader runs at most once per pair.</li>
 *   <li>{@link #snapshot} can return a mix of old and new rates when {@link #replaceAll} runs at the
 *       same time. Read all the pairs under one read lock.</li>
 * </ol>
 */
public class FxRateCache {
    private final ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
    private final Map<String, BigDecimal> rates = new HashMap<>();       // guarded by rw
    private final Function<String, BigDecimal> loader;

    public FxRateCache(Function<String, BigDecimal> loader) {
        this.loader = loader;
    }

    /** The cached rate for {@code pair}, loading it once if it is missing. */
    public BigDecimal rate(String pair) {
        rw.readLock().lock();
        try {
            BigDecimal rate = rates.get(pair);
            if (rate == null) {
                rw.writeLock().lock();          // "upgrade": waits for every reader to leave, including us
                try {
                    rate = loader.apply(pair);
                    rates.put(pair, rate);
                } finally {
                    rw.writeLock().unlock();
                }
            }
            return rate;
        } finally {
            rw.readLock().unlock();
        }
    }

    /** Replaces every cached rate with {@code fresh}, as one step. */
    public void replaceAll(Map<String, BigDecimal> fresh) {
        rw.writeLock().lock();
        try {
            rates.clear();
            rates.putAll(fresh);
        } finally {
            rw.writeLock().unlock();
        }
    }

    /** The current rates for {@code pairs}, all from the same version of the cache. Pairs not cached are left out. */
    public Map<String, BigDecimal> snapshot(Collection<String> pairs) {
        Map<String, BigDecimal> out = new LinkedHashMap<>();
        for (String pair : pairs) {
            rw.readLock().lock();               // one lock per pair: a writer can run between two pairs
            try {
                BigDecimal rate = rates.get(pair);
                if (rate != null) out.put(pair, rate);
            } finally {
                rw.readLock().unlock();
            }
        }
        return out;
    }
}
