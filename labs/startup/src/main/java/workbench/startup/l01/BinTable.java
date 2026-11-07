package workbench.startup.l01;

import java.util.HashMap;
import java.util.Map;

/**
 * Maps a card's BIN (its first six digits) to the bank that issued it.
 *
 * <p>Building the table is slow. In production it parses a large file from the card schemes;
 * here it fills 200,000 rows. The bug: the table is built in the static initializer, so the
 * JVM builds it the first time anything touches this class, even a caller that only wants
 * {@link #version()}. The readiness check that logs the version pays the whole cost.
 *
 * <p>TODO: move the table behind a holder class (a private static nested class with its own
 * static field), so that:
 * <ul>
 *   <li>{@code version()} never builds the table,</li>
 *   <li>the first {@code issuerOf} builds it,</li>
 *   <li>it is built exactly once, even when 8 threads ask at the same moment.</li>
 * </ul>
 * Keep the public signatures and keep calling {@link #build()} to make the table.
 */
public final class BinTable {
    // runs inside BinTable's static initializer (<clinit>), on the first use of the class
    private static final Map<String, String> TABLE = build();

    private BinTable() {
    }

    /** The version of the BIN data. Must not build the table. */
    public static String version() {
        return "bins-2026.11";
    }

    /** The issuer for a card number, or "unknown". Builds the table on first use. */
    public static String issuerOf(String pan) {
        String issuer = TABLE.get(pan.substring(0, 6));
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
