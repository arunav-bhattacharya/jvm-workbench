package workbench.kotlin.l06;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class EventsFromJavaTest {

    @Test
    @DisplayName("Java calls the Kotlin encoder like any static method and gets the same JSON")
    void javaEncodes() {
        String json = JobEventsKt.encodeEvents(List.of(new Printed("job-9", 250)));
        assertThat(json).isEqualTo("[{\"type\":\"printed\",\"jobId\":\"job-9\",\"pages\":250}]");
    }
}
