package workbench.vthreads.l04;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Function;

public class FxRateCache {
    private final Map<String, BigDecimal> rates = new HashMap<>();
    private final Function<String, BigDecimal> ratesService;
    // a j.u.c lock parks a waiting virtual thread instead of pinning it (on every JDK from 21)
    private final ReentrantLock lock = new ReentrantLock();

    public FxRateCache(Function<String, BigDecimal> ratesService) {
        this.ratesService = ratesService;
    }

    public BigDecimal rate(String pair) {
        lock.lock();                 // outside the try: if lock() fails we must not unlock
        try {
            BigDecimal r = rates.get(pair);
            if (r == null) {
                r = ratesService.apply(pair);   // the slow call: the virtual thread can unmount here
                rates.put(pair, r);
            }
            return r;
        } finally {
            lock.unlock();
        }
    }

    public int size() {
        lock.lock();
        try {
            return rates.size();
        } finally {
            lock.unlock();
        }
    }
}
