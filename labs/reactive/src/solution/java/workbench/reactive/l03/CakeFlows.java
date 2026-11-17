package workbench.reactive.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

public final class CakeFlows {
    private CakeFlows() {}

    public static Flux<String> iceAll(Flux<String> cakes, Function<String, Mono<String>> icingMachine) {
        // flatMap: subscribes to inners eagerly and merges results as they finish.
        // The concurrency argument caps how many inners are subscribed at once (default 256).
        return cakes.flatMap(icingMachine, 4);
    }

    public static Flux<String> stackLayers(Flux<String> layers, Function<String, Mono<String>> stacker) {
        // concatMap: subscribes to the next inner only after the previous one completes.
        // An inner error ends the stream, so later layers are never subscribed (never placed).
        return layers.concatMap(stacker);
    }

    public static Flux<String> latestPrices(Flux<String> sizePicks, Function<String, Mono<String>> priceService) {
        // switchMap: each new pick cancels the inner for the previous pick.
        // (switchMap wants a Function returning Publisher exactly, so pass a lambda, not priceService itself)
        return sizePicks.switchMap(size -> priceService.apply(size));
    }
}
