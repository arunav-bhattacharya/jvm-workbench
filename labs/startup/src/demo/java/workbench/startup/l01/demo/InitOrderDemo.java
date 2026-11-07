package workbench.startup.l01.demo;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Prints the moment each static initializer runs. Predict the order before you run it. */
public class InitOrderDemo {
    static final List<String> LOG = new ArrayList<>();

    static Map<String, String> build(String who) {
        LOG.add(who);                                    // the expensive part would go here
        return new HashMap<>(Map.of("411111", "Northwind Bank"));
    }

    /** The table is a static field of the class itself: built on first use of Eager. */
    static class Eager {
        static final Map<String, String> TABLE = build("Eager.<clinit> builds the table");

        static String version() { return "eager-v1"; }
        static Map<String, String> table() { return TABLE; }
    }

    /** The table lives in a nested holder: built on first use of Holder. */
    static class Lazy {
        static { LOG.add("Lazy.<clinit> (no table here)"); }

        static String version() { return "lazy-v1"; }
        static Map<String, String> table() { return Holder.TABLE; }

        private static class Holder {
            static final Map<String, String> TABLE = build("Lazy.Holder.<clinit> builds the table");
        }
    }

    public static void main(String[] args) {
        LOG.add("main starts");
        Eager.version();
        Lazy.version();
        LOG.add("-- both versions read --");
        Lazy.table();
        LOG.add("-- Lazy.table() called --");
        Lazy.table();
        LOG.forEach(System.out::println);
    }
}
