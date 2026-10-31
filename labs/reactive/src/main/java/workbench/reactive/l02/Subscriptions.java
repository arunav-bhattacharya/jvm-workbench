package workbench.reactive.l02;

import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

public final class Subscriptions {
    private Subscriptions() {}

    /**
     * Returns a Mono that emits exactly what {@code source} emits, and adds one to {@code counter}
     * each time something subscribes to it. Building the Mono must not touch the counter.
     */
    public static <T> Mono<T> counted(Mono<T> source, AtomicInteger counter) {
        throw new UnsupportedOperationException("TODO: count each subscription");
    }
}
