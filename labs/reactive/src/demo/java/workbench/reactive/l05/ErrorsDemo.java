package workbench.reactive.l05;

import reactor.core.publisher.Flux;

/** An error ends the stream. The error operators replace what is left with something else. */
public class ErrorsDemo {
    public static void main(String[] args) {
        Flux<Integer> perBox = Flux.just(1, 2, 0, 4).map(i -> 8 / i);         // 8 loaves into i boxes; 0 throws

        perBox.subscribe(v -> System.out.println("raw: " + v), e -> System.out.println("raw: error " + e));

        System.out.println("onErrorReturn: " + perBox.onErrorReturn(-1).collectList().block());

        System.out.println("onErrorResume: " + perBox
                .onErrorResume(e -> Flux.just(100, 200))                      // switch to a backup stream
                .collectList().block());

        perBox.onErrorMap(ArithmeticException.class, e -> new IllegalStateException("bad box count", e))
                .subscribe(v -> { }, e -> System.out.println("onErrorMap: " + e + " caused by " + e.getCause()));
    }
}
