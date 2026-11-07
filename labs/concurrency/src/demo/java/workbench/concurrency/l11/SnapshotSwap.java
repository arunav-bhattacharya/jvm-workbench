package workbench.concurrency.l11;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * An FX rate table refreshed as a whole while readers price payments. Every refresh moves all
 * rates to the same new "version". A reader that sees two versions in one quote saw a half-done refresh.
 */
public class SnapshotSwap {
    static final String[] PAIRS = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF"};

    // 1. shared mutable map, refreshed in place (each put is thread-safe on its own)
    static final Map<String, Long> live = new ConcurrentHashMap<>();
    // 2. an immutable map behind a volatile reference, replaced in one write
    static volatile Map<String, Long> snapshot = Map.of();

    static volatile boolean done;

    public static void main(String[] args) throws InterruptedException {
        Thread refresher = new Thread(() -> {
            for (long version = 1; !done; version++) {
                for (String p : PAIRS) live.put(p, version);          // readers can see a mix
                Map<String, Long> fresh = new HashMap<>();
                for (String p : PAIRS) fresh.put(p, version);
                snapshot = Map.copyOf(fresh);                         // build fully, then publish once
            }
        });
        refresher.start();

        long mixedLive = 0, mixedSnapshot = 0, reads = 0;
        long end = System.nanoTime() + 1_000_000_000L;
        while (System.nanoTime() < end) {
            reads++;
            if (mixed(live)) mixedLive++;
            if (mixed(snapshot)) mixedSnapshot++;                     // one read of the reference: one version
        }
        done = true;
        refresher.join();
        System.out.printf("reads: %,d   mixed versions, shared mutable map: %,d   immutable snapshot: %d%n",
                reads, mixedLive, mixedSnapshot);
    }

    static boolean mixed(Map<String, Long> rates) {
        Long first = rates.get(PAIRS[0]);
        for (String p : PAIRS) if (!java.util.Objects.equals(rates.get(p), first)) return true;
        return false;
    }
}
