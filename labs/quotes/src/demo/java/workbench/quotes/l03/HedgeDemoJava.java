// Java equivalent with Reactor: Mono.firstWithValue races the call against a hedge that starts after 80 ms
package workbench.quotes.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/** 200 quotes from Northbank, all at once, with and without a hedge after 80 ms. Real time. */
public class HedgeDemoJava {
    static final AtomicInteger calls = new AtomicInteger();

    // Northbank: 40 ms, except every 20th call, which takes 600 ms (its slow 5%)
    static Mono<String> northbank() {
        return Mono.defer(() -> {
            int n = calls.incrementAndGet();
            return Mono.delay(Duration.ofMillis(n % 20 == 0 ? 600 : 40)).thenReturn("northbank 1.0845");
        });
    }

    static Mono<String> hedged(Duration after) {
        // the delayed hedge is cancelled before it starts if the first call answers in time
        return Mono.firstWithValue(northbank(), Mono.delay(after).then(northbank()));
    }

    public static void main(String[] args) {
        for (Duration hedgeAfter : new Duration[] {null, Duration.ofMillis(80)}) {
            calls.set(0);
            List<Long> latencies = Flux.range(1, 200)
                    .flatMap(i -> {
                        long t0 = System.nanoTime();
                        Mono<String> q = hedgeAfter == null ? northbank() : hedged(hedgeAfter);
                        return q.map(x -> (System.nanoTime() - t0) / 1_000_000);
                    }, 200)
                    .sort()
                    .collectList().block();
            System.out.printf("%-15s p50 %3d ms   p99 %3d ms   max %3d ms   calls to Northbank: %d%n",
                    hedgeAfter == null ? "no hedge" : "hedge at 80 ms",
                    latencies.get(99), latencies.get(197), latencies.get(199), calls.get());
        }
    }
}
