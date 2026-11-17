package workbench.performance.l06;

import java.util.regex.Pattern;

/** The report step lessons 6 and 7 investigate. It is correct, and it hides three costs. */
public final class SlowReport {
    record Document(String id, String language, String text) { }

    static volatile boolean debugEnabled = false;          // DEBUG logging is off, as it usually is

    private SlowReport() { }

    static void debug(String message) {
        if (debugEnabled) System.out.println(message);
    }

    static long readingSeconds(Document d) {
        if (!Pattern.compile("^[a-z]{2}$").matcher(d.language()).matches())   // a regex compiled per call
            throw new IllegalArgumentException("bad language");
        long words = d.text().split(" ").length;                               // a new String for every word
        long seconds = (words * 60 + 237) / 238;                               // 238 words a minute, rounded up
        debug(String.format("document %s language=%s words=%d seconds=%d",     // formatted, then thrown away
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

    /** Runs readingSeconds on {@code threads} threads until the deadline. */
    static void hammer(int threads, long untilNanos) throws InterruptedException {
        Document[] ds = documents(4_096);
        Thread[] ts = new Thread[threads];
        for (int t = 0; t < threads; t++) {
            int seed = t;
            ts[t] = new Thread(() -> {
                long sink = 0;
                for (int i = seed; System.nanoTime() < untilNanos; i++) sink += readingSeconds(ds[i & 4095]);
                if (sink == 42) System.out.println();
            }, "report-" + t);
            ts[t].start();
        }
        for (Thread t : ts) t.join();
    }
}
