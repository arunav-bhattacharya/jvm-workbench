package workbench.jmm.l01;

import java.util.Map;

/**
 * Holds today's FX rates. A loader thread calls {@link #publish} once at startup.
 * Request threads call {@link #awaitRates()}, which waits until the rates are there.
 *
 * <p>The bug: a request thread that starts waiting before the loader finishes can wait forever.
 * Fix it so a waiting reader always sees the published map. One field needs to change.
 */
public class FxRateBoard {
    private Map<String, Long> rates;   // currency pair -> rate in millionths
    private boolean ready;

    /** Called once, by the loader thread. */
    public void publish(Map<String, Long> loaded) {
        rates = Map.copyOf(loaded);
        ready = true;
    }

    /** Called by request threads. Spins until the loader has published, then returns the rates. */
    public Map<String, Long> awaitRates() {
        while (!ready) {
            // wait for the loader
        }
        return rates;
    }
}
