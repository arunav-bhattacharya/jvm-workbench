package workbench.concurrency.l04;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

/**
 * Holds the latest FX rate per currency pair and tells listeners about every new rate.
 *
 * <p>The lock usage is safe for the board's own state, but {@link #publish} calls listener code
 * while it holds the lock. A listener that asks another thread to read the board stalls, and a
 * listener that subscribes another listener breaks the loop. Fix {@link #publish} so that it never
 * runs listener code while holding {@code lock}. Every listener must still hear about every rate.
 */
public class FxRateBoard {
    private final Object lock = new Object();
    private final Map<String, BigDecimal> rates = new HashMap<>();
    private final List<BiConsumer<String, BigDecimal>> listeners = new ArrayList<>();

    public void subscribe(BiConsumer<String, BigDecimal> listener) {
        synchronized (lock) {
            listeners.add(listener);
        }
    }

    public BigDecimal rate(String pair) {
        synchronized (lock) {
            return rates.get(pair);
        }
    }

    public void publish(String pair, BigDecimal rate) {
        synchronized (lock) {
            rates.put(pair, rate);
            for (BiConsumer<String, BigDecimal> listener : listeners) {
                listener.accept(pair, rate);          // alien code, called while holding our lock
            }
        }
    }
}
