package workbench.reactive.l03;

import reactor.core.publisher.Flux;

/** map and filter are synchronous and work one item at a time. Watch the demand they send upstream. */
public class MapFilterDemo {
    public static void main(String[] args) {
        Flux.range(1, 10)
                .doOnRequest(n -> System.out.println("  oven asked for " + n))
                .filter(loaf -> loaf % 3 == 0)                        // only every third loaf has seeds
                .map(loaf -> "sliced loaf-" + loaf)
                .take(2)                                              // we only want two
                .subscribe(s -> System.out.println("got " + s));

        // Reactor 3.8: a mapper may not return null
        Flux.just("rye", "spelt")
                .map(flour -> flour.equals("rye") ? "dark bread" : null)
                .subscribe(s -> System.out.println("made " + s), e -> System.out.println("error: " + e));
    }
}
