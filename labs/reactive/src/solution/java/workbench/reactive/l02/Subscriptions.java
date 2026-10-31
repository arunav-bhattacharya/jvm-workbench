package workbench.reactive.l02;

import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

public final class Subscriptions {
    private Subscriptions() {}

    public static <T> Mono<T> counted(Mono<T> source, AtomicInteger counter) {
        // doOnSubscribe runs at subscription time, once per subscriber. Mono.defer(() -> { ...; return source; }) works too.
        return source.doOnSubscribe(s -> counter.incrementAndGet());
    }
}
