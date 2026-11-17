package workbench.performance.l02;

public final class DocumentGuards {
    public static final long MAX_WORDS = 10_000_000L;
    public static final int MAX_TITLE_LENGTH = 64;

    private DocumentGuards() { }

    // hot path only: two comparisons and a call to the cold helper (21 bytes of bytecode)
    public static long requireWordCount(long words) {
        if (words <= 0 || words > MAX_WORDS) throw badWordCount(words);
        return words;
    }

    // the same idea: the message is built somewhere C2 doesn't need to look (27 bytes)
    public static String requireTitle(String title) {
        if (title == null || title.isEmpty() || title.length() > MAX_TITLE_LENGTH) throw badTitle(title);
        return title;
    }

    // cold paths: big, rarely run, and no longer counted against the callers' inlining budget.
    // They return the exception, so the caller writes "throw badWordCount(words)" and javac
    // (and the next reader) can see that the method ends there.
    private static IllegalArgumentException badWordCount(long words) {
        return new IllegalArgumentException(
                String.format("word count must be between 1 and %d, got %d", MAX_WORDS, words));
    }

    private static IllegalArgumentException badTitle(String title) {
        String got = title == null ? "null" : String.valueOf(title.length());
        return new IllegalArgumentException(
                String.format("title must be 1 to %d characters, got %s", MAX_TITLE_LENGTH, got));
    }
}
