package workbench.reactive.l08;

import reactor.core.publisher.Flux;

/**
 * A hub that Kafka consumer threads push payment events into, and that dashboards subscribe to.
 * Build it on a {@code Sinks.Many}.
 */
public class PaymentEventHub {

    /**
     * Publishes one event to everyone subscribed right now. Several consumer threads call this at the
     * same time, and no event may be lost.
     */
    public void publish(PaymentEvent event) {
        throw new UnsupportedOperationException("TODO: emit into a sink, safely from many threads");
    }

    /**
     * A hot view of the events. A subscriber sees only the events published after it subscribed; events
     * published while nobody is listening are dropped. Dashboards come and go: the hub must keep working
     * after every subscriber has left, for the next one that arrives.
     */
    public Flux<PaymentEvent> live() {
        throw new UnsupportedOperationException("TODO: expose the sink as a Flux");
    }
}
