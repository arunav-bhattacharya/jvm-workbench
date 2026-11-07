package workbench.startup.l01;

import java.util.HashMap;
import java.util.Map;

/**
 * Maps a card's BIN (its first six digits) to the bank that issued it.
 * Reference answer: the table lives in a holder class, so it is built on first lookup only.
 */
public final class BinTable {

    // The holder idiom. The JVM initializes Holder on the first getstatic of Holder.TABLE,
    // which only issuerOf executes. Class initialization runs under a lock the JVM owns
    // (JLS 12.4.2), so 8 threads asking at once still get exactly one build.
    private static final class Holder {
        static final Map<String, String> TABLE = build();
    }

    private BinTable() {
    }

    /** The version of the BIN data. Touches nothing but a constant. */
    public static String version() {
        return "bins-2026.11";
    }

    /** The issuer for a card number, or "unknown". The first call triggers Holder's initializer. */
    public static String issuerOf(String pan) {
        String issuer = Holder.TABLE.get(pan.substring(0, 6));
        return issuer == null ? "unknown" : issuer;
    }

    /** The expensive part. Records "table-built" so the tests can see when it runs. */
    static Map<String, String> build() {
        InitLog.record("table-built");
        String[] banks = {"Northwind Bank", "Contoso Card Services", "Fabrikam Credit Union"};
        Map<String, String> table = new HashMap<>();
        for (int bin = 400_000; bin < 600_000; bin++) {
            table.put(Integer.toString(bin), banks[bin % banks.length]);
        }
        return table;
    }
}
