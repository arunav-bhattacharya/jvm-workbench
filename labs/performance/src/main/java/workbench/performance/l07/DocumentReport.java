package workbench.performance.l07;

import java.util.regex.Pattern;

/**
 * The report service's busiest step: check a document's language, count its words, and work out how long
 * it takes to read at 238 words a minute, rounded up to the next second. It is correct. Under load it
 * allocates about 2.5 KB per call, and the garbage collector's pauses show up in the slowest calls.
 *
 * <p>Your job: keep the results, the exception and the DEBUG message exactly as they are, and get
 * allocation under 300 bytes per call. Profile first (ReportInvestigation), fix one thing, measure again.
 */
public final class DocumentReport {
    private final DebugLog log;

    public DocumentReport(DebugLog log) {
        this.log = log;
    }

    /** Seconds to read the document. Throws IllegalArgumentException("bad language") unless the language is two letters a to z. */
    public long readingSeconds(Document d) {
        if (!Pattern.compile("^[a-z]{2}$").matcher(d.language()).matches())
            throw new IllegalArgumentException("bad language");
        long words = d.text().split(" ").length;
        long seconds = (words * 60 + 237) / 238;
        log.debug(String.format("document %s language=%s words=%d seconds=%d",   // dropped by the log when DEBUG is off
                d.id(), d.language(), words, seconds));
        return seconds;
    }
}
