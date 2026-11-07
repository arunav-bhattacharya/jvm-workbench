package workbench.reactive.l08;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

/** Turning cold sources into shared ones. */
public final class RateFeeds {
    private RateFeeds() {
    }

    /**
     * {@code upstream} opens a connection to the FX provider for every subscriber. Share it so that:
     * all subscribers use one connection; a subscriber that joins late immediately receives the most
     * recent rate, then the live ones; and when the last subscriber leaves, the connection is closed.
     */
    public static <T> Flux<T> shareWithLatest(Flux<T> upstream) {
        throw new UnsupportedOperationException("TODO: one connection, latest value for late subscribers");
    }

    /**
     * {@code load} reads the fee schedule from the database every time it is subscribed. Load it at most
     * once per {@code ttl}: subscribers within the ttl get the cached value, the first one after it reloads.
     */
    public static <T> Mono<T> cacheFor(Mono<T> load, Duration ttl) {
        throw new UnsupportedOperationException("TODO: cache with a time to live");
    }
}
