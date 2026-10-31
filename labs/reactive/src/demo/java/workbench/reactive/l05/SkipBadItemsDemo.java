package workbench.reactive.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/** Skipping bad items: handle the error inside each item's own Mono, not on the whole stream. */
public class SkipBadItemsDemo {
    public static void main(String[] args) {
        Flux<Integer> amounts = Flux.just(1, 2, 0, 4);

        var whole = amounts.map(i -> 8 / i).onErrorResume(e -> Mono.empty()).collectList().block();
        System.out.println("onErrorResume on the stream: " + whole);

        var perItem = amounts
                .concatMap(i -> Mono.fromCallable(() -> 8 / i)
                        .doOnError(e -> System.out.println("  skipping " + i + ": " + e.getMessage()))
                        .onErrorResume(e -> Mono.empty()))                    // only this item's Mono ends
                .collectList().block();
        System.out.println("onErrorResume per item:      " + perItem);

        var continued = amounts.map(i -> 8 / i)
                .onErrorContinue((e, item) -> System.out.println("  onErrorContinue dropped " + item))
                .collectList().block();
        System.out.println("onErrorContinue:             " + continued);
    }
}
