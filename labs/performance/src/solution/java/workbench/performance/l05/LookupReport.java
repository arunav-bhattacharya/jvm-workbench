package workbench.performance.l05;

import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class LookupReport {
    private static final String NAME = "workbench.Lookup";

    private LookupReport() { }

    private static List<RecordedEvent> lookups(Path jfr) throws IOException {
        // a recording holds hundreds of JDK event types; keep only ours, by name
        return RecordingFile.readAllEvents(jfr).stream()
                .filter(e -> e.getEventType().getName().equals(NAME))
                .toList();
    }

    public static Map<String, Long> missingByShelf(Path jfr) throws IOException {
        Map<String, Long> missing = new TreeMap<>();
        for (RecordedEvent e : lookups(jfr)) {
            if (!e.getBoolean("found")) missing.merge(e.getString("shelf"), 1L, Long::sum);
        }
        return missing;
    }

    public static String slowestShelf(Path jfr) throws IOException {
        return lookups(jfr).stream()
                .max(Comparator.comparing(RecordedEvent::getDuration))   // duration = end - begin
                .map(e -> e.getString("shelf"))
                .orElseThrow(() -> new IllegalStateException("no " + NAME + " events in " + jfr));
    }
}
