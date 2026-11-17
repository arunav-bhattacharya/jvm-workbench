package workbench.performance.l05;

import jdk.jfr.EventType;
import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class FlightRecorderTest {
    private static final String NAME = "workbench.Lookup";

    @TempDir
    Path dir;

    // a tiny document store: three documents, and a basement shelf that takes 100 ms to answer
    private static final DocumentStore STORE = (shelf, title) -> {
        if (shelf.equals("basement")) {
            try { Thread.sleep(100); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }
        return switch (shelf + "/" + title) {
            case "news/weather" -> "Rain in the morning, sun after lunch.";
            case "books/chapter-1" -> "It was a quiet town, and nobody counted the words.";
            case "basement/old-letters" -> "Dear Ana, the roof still leaks.";
            default -> null;                               // this shelf doesn't have it
        };
    };

    // record a few lookups in a real JFR recording, written to a real .jfr file
    private Path recordScenario() throws Exception {
        Path file = dir.resolve("lookups.jfr");
        STORE.fetch("news", "weather");   // warm up: the first call pays one-time JVM set-up costs (string building, class loading)
        try (Recording recording = new Recording()) {
            recording.enable(NAME);
            recording.enable("jdk.ThreadSleep").withThreshold(Duration.ZERO);   // other events in the file too
            recording.start();
            Librarian librarian = new Librarian(STORE);
            librarian.lookup("news", "weather");
            librarian.lookup("news", "yesterday");          // missing
            librarian.lookup("books", "chapter-1");
            librarian.lookup("basement", "old-letters");    // 100 ms at the store
            librarian.lookup("books", "chapter-9");         // missing
            librarian.lookup("books", "chapter-10");        // missing
            recording.stop();
            recording.dump(file);
        }
        return file;
    }

    private static List<RecordedEvent> ours(Path file) throws Exception {
        return RecordingFile.readAllEvents(file).stream()
                .filter(e -> e.getEventType().getName().equals(NAME))
                .toList();
    }

    @Test
    @DisplayName("Librarian still returns the store's answer, text or null")
    void returnsTheStoresAnswer() {
        Librarian librarian = new Librarian(STORE);
        assertThat(librarian.lookup("news", "weather")).isEqualTo("Rain in the morning, sun after lunch.");
        assertThat(librarian.lookup("news", "yesterday")).isNull();
    }

    @Test
    @DisplayName("Librarian records one workbench.Lookup event per call, with shelf, title and outcome")
    void oneEventPerLookup() throws Exception {
        List<RecordedEvent> events = ours(recordScenario());
        assertThat(events).as("workbench.Lookup events in the recording").hasSize(6);
        assertThat(events).extracting(e -> e.getString("shelf"))
                .containsExactly("news", "news", "books", "basement", "books", "books");
        assertThat(events).extracting(e -> e.getString("title"))
                .containsExactly("weather", "yesterday", "chapter-1", "old-letters", "chapter-9", "chapter-10");
        assertThat(events).extracting(e -> e.getBoolean("found"))
                .containsExactly(true, false, true, true, false, false);
    }

    @Test
    @DisplayName("the event type has a label and sits in a Reports category")
    void eventTypeIsDescribed() throws Exception {
        EventType type = ours(recordScenario()).get(0).getEventType();
        assertThat(type.getLabel()).as("@Label on the event class").isNotBlank();
        assertThat(type.getCategoryNames()).as("@Category on the event class").contains("Reports");
        assertThat(type.getField("title").getLabel()).as("@Label on title").isNotBlank();
    }

    @Test
    @DisplayName("the event's duration covers the store call")
    void durationCoversStoreCall() throws Exception {
        RecordedEvent slow = ours(recordScenario()).stream()
                .filter(e -> e.getString("shelf").equals("basement"))
                .findFirst().orElseThrow();
        assertThat(slow.getDuration()).as("duration of the basement lookup")
                .isGreaterThanOrEqualTo(Duration.ofMillis(90));
    }

    @Test
    @DisplayName("LookupReport counts missing documents per shelf and ignores other event types")
    void missingPerShelf() throws Exception {
        Map<String, Long> missing = LookupReport.missingByShelf(recordScenario());
        assertThat(missing).containsOnly(Map.entry("news", 1L), Map.entry("books", 2L));
    }

    @Test
    @DisplayName("LookupReport finds the shelf with the slowest lookup")
    void slowestShelf() throws Exception {
        assertThat(LookupReport.slowestShelf(recordScenario())).isEqualTo("basement");
    }
}
