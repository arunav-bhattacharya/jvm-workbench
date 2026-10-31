package workbench.reactive.l02;

import reactor.core.publisher.Flux;

import java.util.concurrent.atomic.AtomicInteger;

/** Building a pipeline runs none of it. Subscribing runs all of it. */
public class AssemblyDemo {
    public static void main(String[] args) {
        AtomicInteger mapped = new AtomicInteger();

        Flux<Integer> fees = Flux.range(1, 3)
                .map(cents -> {
                    mapped.incrementAndGet();
                    return cents * 100;
                });
        System.out.println("after assembly: map ran " + mapped.get() + " times");

        fees.subscribe(f -> System.out.println("fee " + f));
        System.out.println("after subscribe: map ran " + mapped.get() + " times");

        // A classic bug: the result of filter() is thrown away, so the filter is never part of the chain.
        Flux<Integer> amounts = Flux.just(5, 50, 500);
        amounts.filter(a -> a > 10);
        amounts.subscribe(a -> System.out.println("amount " + a));
    }
}
