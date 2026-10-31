package workbench.executors.l05;

public final class Schedules {
    private Schedules() {}

    public enum Mode { FIXED_RATE, FIXED_DELAY }

    public static long[] startTimes(Mode mode, long initialDelay, long period, long[] durations) {
        long[] starts = new long[durations.length];
        long previousEnd = 0;
        for (int n = 0; n < durations.length; n++) {
            long start;
            if (n == 0) {
                start = initialDelay;
            } else if (mode == Mode.FIXED_RATE) {
                long due = initialDelay + n * period;     // the rate's timetable, fixed in advance
                start = Math.max(due, previousEnd);       // late runs start as soon as the last one ends
            } else {
                start = previousEnd + period;             // the delay counts from the end of the last run
            }
            starts[n] = start;
            previousEnd = start + durations[n];
        }
        return starts;
    }
}
