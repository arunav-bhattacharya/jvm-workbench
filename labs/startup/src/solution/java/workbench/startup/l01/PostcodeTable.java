package workbench.startup.l01;

import java.util.HashMap;
import java.util.Map;

/**
 * Maps a postcode to the depot that delivers parcels there.
 * Reference answer: the table lives in a holder class, so it is built on first lookup only.
 */
public final class PostcodeTable {

    // The holder idiom. The JVM initializes Holder on the first getstatic of Holder.TABLE,
    // which only depotOf executes. Class initialization runs under a lock the JVM owns
    // (JLS 12.4.2), so 8 threads asking at once still get exactly one build.
    private static final class Holder {
        static final Map<String, String> TABLE = build();
    }

    private PostcodeTable() {
    }

    /** The version of the postcode data. Touches nothing but a constant. */
    public static String version() {
        return "postcodes-2026.11";
    }

    /** The depot for a six-digit postcode, or "unknown". The first call triggers Holder's initializer. */
    public static String depotOf(String postcode) {
        String depot = Holder.TABLE.get(postcode);
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
