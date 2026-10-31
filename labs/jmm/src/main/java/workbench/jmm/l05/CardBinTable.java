package workbench.jmm.l05;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Maps the first six digits of a card number (the BIN) to the issuing bank. Loading the table is slow,
 * so it should happen on first use, and only once per JVM.
 *
 * <p>The bug: {@link #instance()} is check-then-act on a plain static field. Under load several
 * threads build their own table. Rewrite it with the holder class idiom. Keep {@link #creations()}
 * cheap: calling it must not build the table.
 */
public final class CardBinTable {
    private static final AtomicInteger CREATIONS = new AtomicInteger();
    private static CardBinTable instance;

    private final Map<String, String> issuersByBin;

    private CardBinTable() {
        CREATIONS.incrementAndGet();
        slowLoad();
        issuersByBin = Map.of("411111", "Northwind Bank", "550000", "Fabrikam Credit", "340000", "Contoso Card Services");
    }

    /** The one table for this JVM, built on first use. */
    public static CardBinTable instance() {
        if (instance == null) {           // check
            instance = new CardBinTable(); // act: several threads can get here
        }
        return instance;
    }

    /** How many tables have been built so far. Must not trigger a build. */
    public static int creations() {
        return CREATIONS.get();
    }

    public String issuerFor(String bin) {
        return issuersByBin.getOrDefault(bin, "unknown");
    }

    // stands in for reading a large BIN file from disk
    private static void slowLoad() {
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
