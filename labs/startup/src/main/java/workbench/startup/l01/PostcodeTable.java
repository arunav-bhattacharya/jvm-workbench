package workbench.startup.l01;

import java.util.HashMap;
import java.util.Map;

/**
 * Maps a postcode to the depot that delivers parcels there.
 *
 * <p>Building the table is slow. In a real service it parses a large file of every postcode in
 * the country; here it fills 200,000 rows. The bug: the table is built in the static initializer,
 * so the JVM builds it the first time anything touches this class, even a caller that only wants
 * {@link #version()}. The health check that logs the version pays the whole cost.
 *
 * <p>TODO: move the table behind a holder class (a private static nested class with its own
 * static field), so that:
 * <ul>
 *   <li>{@code version()} never builds the table,</li>
 *   <li>the first {@code depotOf} builds it,</li>
 *   <li>it is built exactly once, even when 8 threads ask at the same moment.</li>
 * </ul>
 * Keep the public signatures and keep calling {@link #build()} to make the table.
 */
public final class PostcodeTable {
    // runs inside PostcodeTable's static initializer (<clinit>), on the first use of the class
    private static final Map<String, String> TABLE = build();

    private PostcodeTable() {
    }

    /** The version of the postcode data. Must not build the table. */
    public static String version() {
        return "postcodes-2026.11";
    }

    /** The depot for a six-digit postcode, or "unknown". Builds the table on first use. */
    public static String depotOf(String postcode) {
        String depot = TABLE.get(postcode);
        return depot == null ? "unknown" : depot;
    }

    /** The expensive part. Records "table-built" so the tests can see when it runs. */
    static Map<String, String> build() {
        InitLog.record("table-built");
        String[] depots = {"North depot", "River depot", "Hill depot"};
        Map<String, String> table = new HashMap<>();
        for (int code = 400_000; code < 600_000; code++) {
            table.put(Integer.toString(code), depots[code % depots.length]);
        }
        return table;
    }
}
