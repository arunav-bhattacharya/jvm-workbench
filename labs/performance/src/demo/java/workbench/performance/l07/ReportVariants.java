package workbench.performance.l07;

import java.util.regex.Pattern;

/** The report step before and after each round of the investigation. Same results, different costs. */
public final class ReportVariants {
    record Document(String id, String language, String text) { }

    static volatile boolean debugEnabled = false;          // DEBUG is off, as it usually is

    static void debug(String message) {
        if (debugEnabled) System.out.println(message);
    }

    // before: a regex compiled per call, a new String per word, a log line formatted and dropped
    static long slow(Document d) {
        if (!Pattern.compile("^[a-z]{2}$").matcher(d.language()).matches())
            throw new IllegalArgumentException("bad language");
        long words = d.text().split(" ").length;
        long seconds = (words * 60 + 237) / 238;
        debug(String.format("document %s language=%s words=%d seconds=%d",
                d.id(), d.language(), words, seconds));
        return seconds;
    }

    // round 1: compile the pattern once, and format the log line only when DEBUG is on
    static final Pattern LANGUAGE = Pattern.compile("^[a-z]{2}$");

    static long hoisted(Document d) {
        if (!LANGUAGE.matcher(d.language()).matches()) throw new IllegalArgumentException("bad language");
        long words = d.text().split(" ").length;
        long seconds = (words * 60 + 237) / 238;
        if (debugEnabled) debug(String.format("document %s language=%s words=%d seconds=%d",
                d.id(), d.language(), words, seconds));
        return seconds;
    }

    // round 2: the second profile pointed at split; count where words start instead of making each word
    static long countWords(String text) {
        long words = 0;
        boolean inWord = false;
        for (int i = 0; i < text.length(); i++) {
            boolean letter = text.charAt(i) != ' ';
            if (letter && !inWord) words++;
            inWord = letter;
        }
        return words;
    }

    static long scanned(Document d) {
        if (!LANGUAGE.matcher(d.language()).matches()) throw new IllegalArgumentException("bad language");
        long words = countWords(d.text());
        long seconds = (words * 60 + 237) / 238;
        if (debugEnabled) debug(String.format("document %s language=%s words=%d seconds=%d",
                d.id(), d.language(), words, seconds));
        return seconds;
    }

    // round 3, if the budget asks for it: two letters don't need a regex
    static boolean isLanguageCode(String s) {
        return s.length() == 2 && isLower(s.charAt(0)) && isLower(s.charAt(1));
    }

    static boolean isLower(char c) {
        return c >= 'a' && c <= 'z';
    }

    static long noRegex(Document d) {
        if (!isLanguageCode(d.language())) throw new IllegalArgumentException("bad language");
        long words = countWords(d.text());
        long seconds = (words * 60 + 237) / 238;
        if (debugEnabled) debug(String.format("document %s language=%s words=%d seconds=%d",
                d.id(), d.language(), words, seconds));
        return seconds;
    }

    private static final String[] WORDS =
            "the rain came early and the river rose over the old stone bridge before noon".split(" ");
    private static final String[] LANGUAGES = {"en", "fr", "de", "es", "it", "nl"};

    static Document[] documents(int n) {
        Document[] ds = new Document[n];
        for (int i = 0; i < n; i++) {
            StringBuilder text = new StringBuilder();
            for (int w = 0; w < 8 + i % 7; w++) {                               // 8 to 14 words each
                if (w > 0) text.append(' ');
                text.append(WORDS[(i * 7 + w * 3) % WORDS.length]);
            }
            ds[i] = new Document("doc-" + i, LANGUAGES[i % LANGUAGES.length], text.toString());
        }
        return ds;
    }

    private ReportVariants() { }
}
