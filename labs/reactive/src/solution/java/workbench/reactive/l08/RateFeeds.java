package workbench.reactive.l08;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

public final class RateFeeds {
    private RateFeeds() {
    }

    public static <T> Flux<T> shareWithLatest(Flux<T> upstream) {
        // replay(1): a ConnectableFlux that remembers the last item for late subscribers;
        // refCount(): connect on the first subscriber, cancel upstream when the last one leaves
        return upstream.replay(1).refCount();
    }

    public static <T> Mono<T> cacheFor(Mono<T> load, Duration ttl) {
        // the first subscriber triggers the load; the value is replayed until the ttl expires
        return load.cache(ttl);
    }
}
