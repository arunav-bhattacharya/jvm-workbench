package workbench.performance.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.management.ManagementFactory;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DocumentReportTest {
    private static final int BUDGET_BYTES_PER_CALL = 300;

    /** A log with DEBUG off, the usual setting. It counts what it receives. */
    static final class QuietLog implements DebugLog {
        int messages;
        public boolean isDebugEnabled() { return false; }
        public void debug(String message) { messages++; }
    }

    /** A log with DEBUG on, which keeps every message. */
    static final class ChattyLog implements DebugLog {
        final List<String> messages = new ArrayList<>();
        public boolean isDebugEnabled() { return true; }
        public void debug(String message) { messages.add(message); }
    }

    private static final String[] WORDS =
            "the rain came early and the river rose over the old stone bridge before noon".split(" ");
    private static final String[] LANGUAGES = {"en", "fr", "de", "es", "it", "nl"};

    // n documents of minWords to minWords + spread - 1 words, separated by single spaces
    private static Document[] documents(int n, int minWords, int spread) {
        Document[] ds = new Document[n];
        for (int i = 0; i < n; i++) {
            StringBuilder text = new StringBuilder();
            for (int w = 0; w < minWords + i % spread; w++) {
                if (w > 0) text.append(' ');
                text.append(WORDS[(i * 7 + w * 3) % WORDS.length]);
            }
            ds[i] = new Document("doc-" + i, LANGUAGES[i % LANGUAGES.length], text.toString());
        }
        return ds;
    }

    // the rule written independently of your code: words between single spaces, 238 a minute, rounded up
    private static long expectedSeconds(String text) {
        long words = text.split(" ").length;
        return (words * 60 + 237) / 238;
    }

    @Test
    @DisplayName("reading times are unchanged, including texts that land exactly on a whole second")
    void readingTimesAreCorrect() {
        DocumentReport report = new DocumentReport(new QuietLog());
        List<Document> docs = new ArrayList<>(List.of(
                new Document("a", "en", "hello"),
                new Document("b", "fr", String.join(" ", Collections.nCopies(238, "mot"))),   // exactly 60 s
                new Document("c", "de", String.join(" ", Collections.nCopies(239, "wort")))));
        docs.addAll(List.of(documents(600, 1, 300)));
        for (Document d : docs) {
            assertThat(report.readingSeconds(d)).as("seconds for %s", d.id()).isEqualTo(expectedSeconds(d.text()));
        }
    }

    @Test
    @DisplayName("languages that are not two letters a to z are still rejected")
    void badLanguageRejected() {
        DocumentReport report = new DocumentReport(new QuietLog());
        for (String bad : new String[] {"EN", "eng", "e1", "", "f"}) {
            assertThatThrownBy(() -> report.readingSeconds(new Document("d", bad, "some words")))
                    .as("language '%s'", bad)
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("bad language");
        }
    }

    @Test
    @DisplayName("with DEBUG on, the log line is exactly the same as before")
    void debugMessageUnchanged() {
        ChattyLog log = new ChattyLog();
        new DocumentReport(log).readingSeconds(
                new Document("doc-7", "fr", "the rain came early and the river rose over the old stone"));
        assertThat(log.messages).containsExactly("document doc-7 language=fr words=12 seconds=4");
    }

    @Test
    @DisplayName("allocates under 300 bytes per call once warm (measured with the per-thread allocation counter)")
    void allocationBudget() {
        DocumentReport report = new DocumentReport(new QuietLog());
        Document[] ds = documents(1_024, 8, 7);                     // short texts, like the busy path: 8 to 14 words
        var threads = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
        int calls = 100_000;
        long sink = 0;
        List<Double> rounds = new ArrayList<>();
        // allocation only settles once C2 has compiled readingSeconds, so measure 10 rounds and judge the best one;
        // a busy machine can delay the compile, but it can't make warm code allocate less than it does
        for (int round = 0; round < 10; round++) {
            long before = threads.getCurrentThreadAllocatedBytes();
            for (int i = 0; i < calls; i++) sink += report.readingSeconds(ds[i & 1023]);
            rounds.add((double) (threads.getCurrentThreadAllocatedBytes() - before) / calls);
        }
        double best = rounds.stream().mapToDouble(Double::doubleValue).min().orElseThrow();

        assertThat(sink).isPositive();
        assertThat(best).as("bytes per readingSeconds call (best of rounds %s)", rounds)
                .isLessThan(BUDGET_BYTES_PER_CALL);
    }
}
