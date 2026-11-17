package workbench.performance.l02;

/**
 * Checks that run on every document the report service receives. Both are correct, and both are
 * too big to inline at a call site C2 doesn't consider hot: C2 counts the bytecode of the error
 * path too, even though that path almost never runs.
 *
 * <p>Your job: make {@link #requireWordCount} and {@link #requireTitle} at most 35 bytes
 * of bytecode each ({@code MaxInlineSize}), without changing what they return or the exact
 * exception messages. Check the size with
 * {@code javap -c -p -cp performance/build/classes/java/main workbench.performance.l02.DocumentGuards}.
 */
public final class DocumentGuards {
    public static final long MAX_WORDS = 10_000_000L;
    public static final int MAX_TITLE_LENGTH = 64;

    private DocumentGuards() { }

    /**
     * Returns {@code words} when it is between 1 and {@link #MAX_WORDS}. Otherwise throws
     * {@code IllegalArgumentException("word count must be between 1 and 10000000, got <words>")}.
     */
    public static long requireWordCount(long words) {
        if (words <= 0 || words > MAX_WORDS) {
            throw new IllegalArgumentException(
                    String.format("word count must be between 1 and %d, got %d", MAX_WORDS, words));
        }
        return words;
    }

    /**
     * Returns {@code title} when it has 1 to {@link #MAX_TITLE_LENGTH} characters. Otherwise throws
     * {@code IllegalArgumentException("title must be 1 to 64 characters, got <n>")},
     * where {@code <n>} is the length, or {@code null} when the title is null.
     */
    public static String requireTitle(String title) {
        if (title == null || title.isEmpty() || title.length() > MAX_TITLE_LENGTH) {
            String got = title == null ? "null" : String.valueOf(title.length());
            throw new IllegalArgumentException(
                    String.format("title must be 1 to %d characters, got %s", MAX_TITLE_LENGTH, got));
        }
        return title;
    }
}
