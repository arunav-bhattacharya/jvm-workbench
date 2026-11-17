// Java equivalent of OperatorOrder.kt: a synchronous Flux also moves one item through the whole
// chain before the source produces the next one, and nothing runs until subscribe().
package workbench.coroutines.l07;

import reactor.core.publisher.Flux;

public class OperatorOrderJava {
    public static void main(String[] args) {
        // weights in grams from the kitchen scale; a negative reading means it wasn't set to zero
        Flux<String> pipeline = Flux.just(250L, -40L, 1_200L)
            .doOnNext(g -> System.out.println("emit    " + g))
            .filter(g -> g > 0).doOnNext(g -> System.out.println("  filter passed " + g))
            .map(g -> String.format("%.2f kg", g / 1_000.0)).doOnNext(s -> System.out.println("    map   -> " + s));
        System.out.println("pipeline built: no line above has printed yet");
        pipeline.subscribe(s -> System.out.println("      subscribe " + s));
    }
}
