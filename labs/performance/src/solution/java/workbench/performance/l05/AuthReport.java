package workbench.performance.l05;

import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class AuthReport {
    private static final String NAME = "workbench.Authorization";

    private AuthReport() { }

    private static List<RecordedEvent> authorizations(Path jfr) throws IOException {
        // a recording holds hundreds of JDK event types; keep only ours, by name
        return RecordingFile.readAllEvents(jfr).stream()
                .filter(e -> e.getEventType().getName().equals(NAME))
                .toList();
    }

    public static Map<String, Long> declinesByMerchant(Path jfr) throws IOException {
        Map<String, Long> declines = new TreeMap<>();
        for (RecordedEvent e : authorizations(jfr)) {
            if (!e.getBoolean("approved")) declines.merge(e.getString("merchant"), 1L, Long::sum);
        }
        return declines;
    }

    public static String slowestMerchant(Path jfr) throws IOException {
        return authorizations(jfr).stream()
                .max(Comparator.comparing(RecordedEvent::getDuration))   // duration = end - begin
                .map(e -> e.getString("merchant"))
                .orElseThrow(() -> new IllegalStateException("no " + NAME + " events in " + jfr));
    }
}
