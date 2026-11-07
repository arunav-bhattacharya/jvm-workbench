package workbench.startup.l01;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * A log the tests can read: code appends an event when it does expensive start-up work.
 * Don't change this class.
 */
public final class InitLog {
    private static final List<String> EVENTS = new CopyOnWriteArrayList<>();

    private InitLog() {
    }

    public static void record(String event) {
        EVENTS.add(event);
    }

    public static List<String> events() {
        return List.copyOf(EVENTS);
    }

    public static void clear() {
        EVENTS.clear();
    }
}
