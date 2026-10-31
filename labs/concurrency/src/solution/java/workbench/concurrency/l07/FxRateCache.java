package workbench.concurrency.l07;

import java.math.BigDecimal;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.function.Function;

public class FxRateCache {
    private final ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
    private final Map<String, BigDecimal> rates = new HashMap<>();
    private final Function<String, BigDecimal> loader;

    public FxRateCache(Function<String, BigDecimal> loader) {
        this.loader = loader;
    }

    public BigDecimal rate(String pair) {
        // 1. fast path: many readers at once
        rw.readLock().lock();
        try {
            BigDecimal rate = rates.get(pair);
            if (rate != null) return rate;
        } finally {
            rw.readLock().unlock();             // 2. let go of the read lock BEFORE asking for the write lock
        }
        rw.writeLock().lock();
        try {
            // 3. re-check: another thread may have loaded it while we held no lock
            BigDecimal rate = rates.get(pair);
            if (rate == null) {
                rate = loader.apply(pair);
                rates.put(pair, rate);
            }
            return rate;
        } finally {
            rw.writeLock().unlock();
        }
    }

    public void replaceAll(Map<String, BigDecimal> fresh) {
        rw.writeLock().lock();
        try {
            rates.clear();
            rates.putAll(fresh);
        } finally {
            rw.writeLock().unlock();
        }
    }

    public Map<String, BigDecimal> snapshot(Collection<String> pairs) {
        rw.readLock().lock();                   // one read lock for the whole snapshot
        try {
            Map<String, BigDecimal> out = new LinkedHashMap<>();
            for (String pair : pairs) {
                BigDecimal rate = rates.get(pair);
                if (rate != null) out.put(pair, rate);
            }
            return out;
        } finally {
            rw.readLock().unlock();
        }
    }
}
