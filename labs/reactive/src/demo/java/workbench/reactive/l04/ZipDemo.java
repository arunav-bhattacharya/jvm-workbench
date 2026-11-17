package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

/** zip pairs by position. Mono.zip with an empty source completes empty, and cancels the others. */
public class ZipDemo {
    public static void main(String[] args) {
        System.out.println("Flux.zip: " + Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b")).collectList().block());

        Mono<String> price = Mono.delay(Duration.ofMillis(200)).thenReturn("24.00")
                .doOnCancel(() -> System.out.println("  price lookup cancelled"));
        Mono<String> deliveryFee = Mono.delay(Duration.ofMillis(100)).thenReturn("3.50");
        Mono<String> discount = Mono.empty();                                // this customer has no discount

        Mono.zip(price, deliveryFee, discount)
                .doOnSuccess(t -> System.out.println("Mono.zip result: " + t))  // null means "completed empty"
                .block();

        Mono.zip(price, deliveryFee, discount.defaultIfEmpty("0.00"))
                .doOnSuccess(t -> System.out.println("with defaultIfEmpty: " + t))
                .block();

        try {
            Mono.zip(price, deliveryFee, discount.switchIfEmpty(Mono.error(new IllegalStateException("missing discount"))))
                    .block();
        } catch (IllegalStateException e) {
            System.out.println("with switchIfEmpty: " + e.getMessage());
        }
    }
}
