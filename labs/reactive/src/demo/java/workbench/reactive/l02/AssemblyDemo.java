package workbench.reactive.l02;

import reactor.core.publisher.Flux;

import java.util.concurrent.atomic.AtomicInteger;

/** Building a pipeline runs none of it. Subscribing runs all of it. */
public class AssemblyDemo {
    public static void main(String[] args) {
        AtomicInteger mapped = new AtomicInteger();

        Flux<Integer> pricesInCents = Flux.range(1, 3)
                .map(euros -> {
                    mapped.incrementAndGet();
                    return euros * 100;
                });
        System.out.println("after assembly: map ran " + mapped.get() + " times");

        pricesInCents.subscribe(p -> System.out.println("price " + p + " cents"));
        System.out.println("after subscribe: map ran " + mapped.get() + " times");

        // A classic bug: the result of filter() is thrown away, so the filter is never part of the chain.
        Flux<Integer> orderSizes = Flux.just(5, 50, 500);
        orderSizes.filter(loaves -> loaves > 10);
        orderSizes.subscribe(loaves -> System.out.println("big order: " + loaves + " loaves"));
    }
}
