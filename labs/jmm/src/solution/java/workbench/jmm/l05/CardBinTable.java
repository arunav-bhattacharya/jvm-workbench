package workbench.jmm.l05;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

public final class CardBinTable {
    private static final AtomicInteger CREATIONS = new AtomicInteger();

    private final Map<String, String> issuersByBin;

    private CardBinTable() {
        CREATIONS.incrementAndGet();
        slowLoad();
        issuersByBin = Map.of("411111", "Northwind Bank", "550000", "Fabrikam Credit", "340000", "Contoso Card Services");
    }

    // The JVM initializes Holder once, under its class-initialization lock, the first time
    // instance() touches Holder.INSTANCE. Every thread then sees the finished table.
    private static final class Holder {
        static final CardBinTable INSTANCE = new CardBinTable();
    }

    public static CardBinTable instance() {
        return Holder.INSTANCE;
    }

    // touches only CREATIONS, so it never triggers Holder's initialization
    public static int creations() {
        return CREATIONS.get();
    }

    public String issuerFor(String bin) {
        return issuersByBin.getOrDefault(bin, "unknown");
    }

    private static void slowLoad() {
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
