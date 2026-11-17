package workbench.performance.l03;

/** The code under test in this lab's benchmarks: the report service's reading-time maths. Same file in src/main and src/solution. */
public final class ReadingMath {
    private ReadingMath() { }

    /** Seconds to read {@code words} words silently, at 238 words a minute, rounded up. */
    public static long readingSeconds(long words) {
        return (words * 60 + 237) / 238;
    }

    /** Seconds to read {@code words} words aloud, at 130 words a minute, rounded up. */
    public static long speakingSeconds(long words) {
        return (words * 60 + 129) / 130;
    }
}
