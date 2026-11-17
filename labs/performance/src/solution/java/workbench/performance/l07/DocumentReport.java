package workbench.performance.l07;

import java.util.regex.Pattern;

public final class DocumentReport {
    // round 1: the pattern is compiled once, not per call
    private static final Pattern LANGUAGE = Pattern.compile("^[a-z]{2}$");

    private final DebugLog log;

    public DocumentReport(DebugLog log) {
        this.log = log;
    }

    public long readingSeconds(Document d) {
        if (!LANGUAGE.matcher(d.language()).matches())              // what's left: one Matcher, about 136 bytes
            throw new IllegalArgumentException("bad language");
        long words = countWords(d.text());
        long seconds = (words * 60 + 237) / 238;
        if (log.isDebugEnabled()) {                                 // round 1: format only when someone reads it
            log.debug(String.format("document %s language=%s words=%d seconds=%d",
                    d.id(), d.language(), words, seconds));
        }
        return seconds;
    }

    // round 2: the re-profile showed split next; count where words start instead of making each word
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
}
