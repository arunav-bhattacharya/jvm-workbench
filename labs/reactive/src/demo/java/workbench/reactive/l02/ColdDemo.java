package workbench.reactive.l02;

import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

/** A cold Mono does its work again for every subscriber. Here the work is a card charge. */
public class ColdDemo {
    static final AtomicInteger charges = new AtomicInteger();

    static Mono<String> charge(String paymentId) {
        return Mono.fromCallable(() -> {
            int n = charges.incrementAndGet();
            System.out.println("  issuer: charging " + paymentId + " (charge #" + n + ")");
            return "receipt-" + n;
        });
    }

    public static void main(String[] args) {
        Mono<String> charge = charge("pay-42");

        charge.subscribe(r -> System.out.println("audit log: " + r));   // subscriber 1
        String receipt = charge.block();                                // subscriber 2
        System.out.println("returned to caller: " + receipt);
        System.out.println("charges made: " + charges.get());
    }
}
