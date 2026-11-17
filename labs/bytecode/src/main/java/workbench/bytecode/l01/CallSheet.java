package workbench.bytecode.l01;

import java.util.Map;

/**
 * The theatre's call sheet: how many minutes before the curtain goes up each role must arrive.
 * One shared instance.
 *
 * <p>A role the table doesn't list should get the default call, 60 minutes. It gets 0, so that
 * player is told to arrive as the curtain goes up, and nothing throws. Read the static
 * initializer from top to bottom, the way the JVM runs it, and fix the class without changing
 * any number.
 */
public final class CallSheet {
    private static final Map<String, Integer> MINUTES_BY_ROLE = Map.of("LEAD", 90, "CHORUS", 45);

    public static final CallSheet INSTANCE = new CallSheet();

    // not a compile-time constant (it calls a method), so it is assigned when <clinit> reaches this line
    private static final int DEFAULT_MINUTES = Integer.parseInt(System.getProperty("calls.default.minutes", "60"));
    // a compile-time constant: javac copies "minutes" into every place that reads it
    private static final String UNIT = "minutes";

    private final int fallbackMinutes;
    private final String unit;

    private CallSheet() {
        fallbackMinutes = DEFAULT_MINUTES;
        unit = UNIT;
    }

    /** Minutes before curtain-up that a player in this {@code role}, such as {@code "LEAD"}, must arrive. */
    public int minutesBefore(String role) {
        return MINUTES_BY_ROLE.getOrDefault(role, fallbackMinutes);
    }

    public String unit() {
        return unit;
    }
}
