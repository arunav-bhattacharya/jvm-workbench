package workbench.performance.l05;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;

/** Answers two questions from a .jfr file, using the {@code workbench.Lookup} events in it. */
public final class LookupReport {
    private LookupReport() { }

    /**
     * Lookups that found nothing, per shelf. Shelves where every lookup found its document are left out.
     * Read the file with {@code jdk.jfr.consumer.RecordingFile} and ignore every other event type.
     */
    public static Map<String, Long> missingByShelf(Path jfr) throws IOException {
        throw new UnsupportedOperationException("TODO: count workbench.Lookup events with found == false");
    }

    /** The shelf whose single slowest lookup took the longest (by event duration). */
    public static String slowestShelf(Path jfr) throws IOException {
        throw new UnsupportedOperationException("TODO: find the event with the longest getDuration()");
    }
}
