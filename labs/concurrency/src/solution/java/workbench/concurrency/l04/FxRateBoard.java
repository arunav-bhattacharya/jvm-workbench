package workbench.concurrency.l04;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

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
        List<BiConsumer<String, BigDecimal>> toNotify;
        synchronized (lock) {
            // 1. under the lock: change our own state and take a copy of the listeners. Short and fast.
            rates.put(pair, rate);
            toNotify = List.copyOf(listeners);
        }
        // 2. outside the lock: run code we don't control. It can block, call back in, or subscribe.
        for (BiConsumer<String, BigDecimal> listener : toNotify) {
            listener.accept(pair, rate);
        }
    }
}
