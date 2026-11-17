package workbench.bytecode.l01;

import java.util.Map;

public final class CallSheet {
    private static final Map<String, Integer> MINUTES_BY_ROLE = Map.of("LEAD", 90, "CHORUS", 45);
    // <clinit> runs the static initializers in source order, so every field the constructor
    // reads must be assigned ABOVE the line that calls the constructor
    private static final int DEFAULT_MINUTES = Integer.parseInt(System.getProperty("calls.default.minutes", "60"));
    private static final String UNIT = "minutes";

    // moved below the fields it needs
    public static final CallSheet INSTANCE = new CallSheet();

    private final int fallbackMinutes;
    private final String unit;

    private CallSheet() {
        fallbackMinutes = DEFAULT_MINUTES;
        unit = UNIT;
    }

    public int minutesBefore(String role) {
        return MINUTES_BY_ROLE.getOrDefault(role, fallbackMinutes);
    }

    public String unit() {
        return unit;
    }
}
