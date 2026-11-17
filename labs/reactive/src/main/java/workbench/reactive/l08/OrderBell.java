package workbench.reactive.l08;

import reactor.core.publisher.Flux;

/**
 * A bell that the shop's tills ring with order events, and that kitchen screens listen to.
 * Build it on a {@code Sinks.Many}.
 */
public class OrderBell {

    /**
     * Rings the bell with one event, for everyone listening right now. Several till threads call this at the
     * same time, and no event may be lost.
     */
    public void ring(OrderEvent event) {
        throw new UnsupportedOperationException("TODO: emit into a sink, safely from many threads");
    }

    /**
     * A hot view of the events. A listener hears only the events rung after it started listening; events rung
     * while nobody is listening are dropped. Screens come and go: the bell must keep working after every
     * listener has left, for the next one that arrives.
     */
    public Flux<OrderEvent> live() {
        throw new UnsupportedOperationException("TODO: expose the sink as a Flux");
    }
}
