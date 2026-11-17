package workbench.reactive.l02;

import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

/** A cold Mono does its work again for every subscriber. Here the work is baking a cake. */
public class ColdDemo {
    static final AtomicInteger baked = new AtomicInteger();

    static Mono<String> bake(String orderId) {
        return Mono.fromCallable(() -> {
            int n = baked.incrementAndGet();
            System.out.println("  oven: baking the cake for " + orderId + " (cake #" + n + ")");
            return "cake-" + n;
        });
    }

    public static void main(String[] args) {
        Mono<String> cake = bake("order-42");

        cake.subscribe(c -> System.out.println("shop log: " + c));   // subscriber 1
        String handedOver = cake.block();                           // subscriber 2
        System.out.println("handed to the customer: " + handedOver);
        System.out.println("cakes baked: " + baked.get());
    }
}
