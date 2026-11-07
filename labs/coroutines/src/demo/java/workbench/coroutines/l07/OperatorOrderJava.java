// Java equivalent of OperatorOrder.kt: a synchronous Flux also moves one item through the whole
// chain before the source produces the next one, and nothing runs until subscribe().
package workbench.coroutines.l07;

import reactor.core.publisher.Flux;

public class OperatorOrderJava {
    public static void main(String[] args) {
        // amounts in cents; refunds are negative
        Flux<String> pipeline = Flux.just(4_250L, -990L, 12_000L)
            .doOnNext(a -> System.out.println("emit    " + a))
            .filter(a -> a > 0).doOnNext(a -> System.out.println("  filter passed " + a))
            .map(a -> String.format("EUR %.2f", a / 100.0)).doOnNext(s -> System.out.println("    map   -> " + s));
        System.out.println("pipeline built: no line above has printed yet");
        pipeline.subscribe(s -> System.out.println("      subscribe " + s));
    }
}
