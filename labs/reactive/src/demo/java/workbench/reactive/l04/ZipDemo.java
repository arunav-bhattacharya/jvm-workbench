package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

/** zip pairs by position. Mono.zip with an empty source completes empty, and cancels the others. */
public class ZipDemo {
    public static void main(String[] args) {
        System.out.println("Flux.zip: " + Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b")).collectList().block());

        Mono<String> fxRate = Mono.delay(Duration.ofMillis(200)).thenReturn("1.08")
                .doOnCancel(() -> System.out.println("  fx rate call cancelled"));
        Mono<String> fee = Mono.delay(Duration.ofMillis(100)).thenReturn("0.30");
        Mono<String> limit = Mono.empty();                                   // no limit configured

        Mono.zip(fxRate, fee, limit)
                .doOnSuccess(t -> System.out.println("Mono.zip result: " + t))  // null means "completed empty"
                .block();

        try {
            Mono.zip(fxRate, fee, limit.switchIfEmpty(Mono.error(new IllegalStateException("missing limit"))))
                    .block();
        } catch (IllegalStateException e) {
            System.out.println("with switchIfEmpty: " + e.getMessage());
        }
    }
}
