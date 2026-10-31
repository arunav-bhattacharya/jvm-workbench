package workbench.reactive.l03;

import reactor.core.publisher.Flux;

/** map and filter are synchronous and work one item at a time. Watch the demand they send upstream. */
public class MapFilterDemo {
    public static void main(String[] args) {
        Flux.range(1, 10)
                .doOnRequest(n -> System.out.println("  source asked for " + n))
                .filter(amount -> amount % 3 == 0)                    // drops 1, 2, 4, 5, ...
                .map(amount -> "EUR " + amount * 10)
                .take(2)                                              // we only want two
                .subscribe(s -> System.out.println("got " + s));

        // Reactor 3.8: a mapper may not return null
        Flux.just("4111", "5500")
                .map(bin -> bin.startsWith("4") ? "VISA" : null)
                .subscribe(s -> System.out.println("scheme " + s), e -> System.out.println("error: " + e));
    }
}
