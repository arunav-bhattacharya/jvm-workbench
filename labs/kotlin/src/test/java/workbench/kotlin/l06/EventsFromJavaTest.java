package workbench.kotlin.l06;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class EventsFromJavaTest {

    @Test
    @DisplayName("Java calls the Kotlin encoder like any static method and gets the same JSON")
    void javaEncodes() {
        String json = PaymentEventsKt.encodeEvents(List.of(new Captured("pay_9", 250L)));
        assertThat(json).isEqualTo("[{\"type\":\"captured\",\"paymentId\":\"pay_9\",\"amountMinor\":250}]");
    }
}
