package workbench.jmm.l01;

import java.util.Map;

public class FxRateBoard {
    private Map<String, Long> rates;   // plain is enough: it is written before the volatile write below
    private volatile boolean ready;    // the flag the reader spins on is the one that must be volatile

    public void publish(Map<String, Long> loaded) {
        rates = Map.copyOf(loaded);    // 1. write the data
        ready = true;                  // 2. then flip the volatile flag; this write carries step 1 with it
    }

    public Map<String, Long> awaitRates() {
        while (!ready) {               // volatile read: re-read on every pass
            Thread.onSpinWait();       // a hint to the CPU that this is a busy-wait
        }
        return rates;                  // read after seeing ready == true, so it sees the map
    }
}
