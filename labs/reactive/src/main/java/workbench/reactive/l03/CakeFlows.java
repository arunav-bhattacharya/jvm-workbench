package workbench.reactive.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

/**
 * Three stations on the bakery's belt, three different needs. Each body is one line: pick the
 * operator that fits. Choose between {@code flatMap} (with or without a concurrency argument),
 * {@code concatMap}, {@code flatMapSequential} and {@code switchMap}.
 */
public final class CakeFlows {
    private CakeFlows() {}

    /**
     * Sends every cake to the icing machine. Iced cakes may come back in any order.
     * The machine has 4 nozzles, so it takes at most 4 cakes at once, and we want to use all 4.
     */
    public static Flux<String> iceAll(Flux<String> cakes, Function<String, Mono<String>> icingMachine) {
        throw new UnsupportedOperationException("TODO: any order, at most 4 cakes at the machine");
    }

    /**
     * Stacks the layers of a tall cake. A layer may only go on after the one below it has set,
     * results come back in stacking order, and after a layer fails no later layer may be placed.
     */
    public static Flux<String> stackLayers(Flux<String> layers, Function<String, Mono<String>> stacker) {
        throw new UnsupportedOperationException("TODO: strictly one at a time, in order");
    }

    /**
     * A customer on the bakery's website picks a cake size in a list; each pick asks the price
     * service for a price. Only the price for the most recent pick matters: a price still on its way
     * when the customer picks again must be abandoned (cancelled), and must never be shown.
     */
    public static Flux<String> latestPrices(Flux<String> sizePicks, Function<String, Mono<String>> priceService) {
        throw new UnsupportedOperationException("TODO: only the latest pick counts");
    }
}
