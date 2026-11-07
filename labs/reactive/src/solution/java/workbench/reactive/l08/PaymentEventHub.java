package workbench.reactive.l08;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

import java.time.Duration;

public class PaymentEventHub {
    // multicast: every current subscriber gets each new event, late subscribers don't see old ones.
    // directBestEffort keeps no warm-up buffer and survives having zero subscribers; the default
    // onBackpressureBuffer() flavour shuts down for good when its last subscriber leaves.
    // (A subscriber that doesn't keep up misses events, and only that subscriber.)
    private final Sinks.Many<PaymentEvent> events = Sinks.many().multicast().directBestEffort();

    public void publish(PaymentEvent event) {
        // tryEmitNext fails with FAIL_NON_SERIALIZED when two threads emit at once; this handler
        // spins and retries until the sink is free (for up to 1 s). A new handler per call, as the Javadoc asks.
        events.emitNext(event, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)));
    }

    public Flux<PaymentEvent> live() {
        return events.asFlux();                                  // a read-only view: callers can't emit
    }
}
