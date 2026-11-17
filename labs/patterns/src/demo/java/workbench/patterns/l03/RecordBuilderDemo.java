package workbench.patterns.l03;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/** A record with a small builder: the record checks, the builder only collects. */
public class RecordBuilderDemo {

    record DeliveryRequest(String address, String speed, Map<String, String> notes, Duration window, int retries) {
        DeliveryRequest {                                    // every path to a DeliveryRequest runs this
            Objects.requireNonNull(address, "address");
            notes = Map.copyOf(notes);                       // really unmodifiable
            if (retries < 0) throw new IllegalArgumentException("retries must be >= 0, was " + retries);
        }

        DeliveryRequest withWindow(Duration w) {             // a hand-written "wither"
            return new DeliveryRequest(address, speed, notes, w, retries);
        }

        DeliveryRequest withRetries(int n) {
            return new DeliveryRequest(address, speed, notes, window, n);
        }

        static Builder builder(String address) { return new Builder(address); }

        static final class Builder {
            private final String address;
            private String speed = "STANDARD";
            private final Map<String, String> notes = new LinkedHashMap<>();
            private Duration window = Duration.ofHours(2);
            private int retries = 0;

            private Builder(String address) { this.address = address; }
            Builder speed(String s) { speed = s; return this; }
            Builder note(String k, String v) { notes.put(k, v); return this; }
            Builder window(Duration w) { window = w; return this; }
            Builder retries(int n) { retries = n; return this; }
            DeliveryRequest build() { return new DeliveryRequest(address, speed, notes, window, retries); }
        }
    }

    public static void main(String[] args) {
        DeliveryRequest req = DeliveryRequest.builder("12 Mill Lane")
                .speed("EXPRESS")
                .note("door", "blue gate")
                .retries(2)
                .build();
        System.out.println("built:        " + req);
        System.out.println("narrower:     " + req.withWindow(Duration.ofMinutes(30)).window());

        try {
            req.notes().put("dog", "friendly");
        } catch (UnsupportedOperationException e) {
            System.out.println("notes:        unmodifiable");
        }

        try {
            req.withRetries(-1);                              // the wither can't skip the check either
        } catch (IllegalArgumentException e) {
            System.out.println("wither:       " + e.getMessage());
        }
    }
}
