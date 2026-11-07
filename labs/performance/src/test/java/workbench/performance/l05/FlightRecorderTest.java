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
    private static final String NAME = "workbench.Authorization";

    @TempDir
    Path dir;

    // the issuer approves anything under 1,000.00 and takes 40 ms for merchant m_slow
    private static final Issuer ISSUER = (merchant, cents) -> {
        if (merchant.equals("m_slow")) {
            try { Thread.sleep(40); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }
        return cents < 100_000;
    };

    // record a few authorizations in a real JFR recording, written to a real .jfr file
    private Path recordScenario() throws Exception {
        Path file = dir.resolve("auth.jfr");
        try (Recording recording = new Recording()) {
            recording.enable(NAME);
            recording.enable("jdk.ThreadSleep").withThreshold(Duration.ZERO);   // other events in the file too
            recording.start();
            Authorizer authorizer = new Authorizer(ISSUER);
            authorizer.authorize("m_coffee", 450);
            authorizer.authorize("m_coffee", 250_000);      // declined
            authorizer.authorize("m_books", 1_999);
            authorizer.authorize("m_slow", 5_000);          // 40 ms at the issuer
            authorizer.authorize("m_books", 120_000);       // declined
            authorizer.authorize("m_books", 990_000);       // declined
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
    @DisplayName("Authorizer records one workbench.Authorization event per call, with merchant, amount and outcome")
    void oneEventPerAuthorization() throws Exception {
        List<RecordedEvent> events = ours(recordScenario());
        assertThat(events).as("workbench.Authorization events in the recording").hasSize(6);
        assertThat(events).extracting(e -> e.getString("merchant"))
                .containsExactly("m_coffee", "m_coffee", "m_books", "m_slow", "m_books", "m_books");
        assertThat(events).extracting(e -> e.getLong("amountCents"))
                .containsExactly(450L, 250_000L, 1_999L, 5_000L, 120_000L, 990_000L);
        assertThat(events).extracting(e -> e.getBoolean("approved"))
                .containsExactly(true, false, true, true, false, false);
    }

    @Test
    @DisplayName("the event type has a label and sits in a Payments category")
    void eventTypeIsDescribed() throws Exception {
        EventType type = ours(recordScenario()).get(0).getEventType();
        assertThat(type.getLabel()).as("@Label on the event class").isNotBlank();
        assertThat(type.getCategoryNames()).as("@Category on the event class").contains("Payments");
        assertThat(type.getField("amountCents").getLabel()).as("@Label on amountCents").isNotBlank();
    }

    @Test
    @DisplayName("the event's duration covers the issuer call")
    void durationCoversIssuerCall() throws Exception {
        RecordedEvent slow = ours(recordScenario()).stream()
                .filter(e -> e.getString("merchant").equals("m_slow"))
                .findFirst().orElseThrow();
        assertThat(slow.getDuration()).as("duration of m_slow's authorization")
                .isGreaterThanOrEqualTo(Duration.ofMillis(35));
    }

    @Test
    @DisplayName("AuthReport counts declines per merchant and ignores other event types")
    void declinesPerMerchant() throws Exception {
        Map<String, Long> declines = AuthReport.declinesByMerchant(recordScenario());
        assertThat(declines).containsOnly(Map.entry("m_coffee", 1L), Map.entry("m_books", 2L));
    }

    @Test
    @DisplayName("AuthReport finds the merchant with the slowest authorization")
    void slowestMerchant() throws Exception {
        assertThat(AuthReport.slowestMerchant(recordScenario())).isEqualTo("m_slow");
    }
}
