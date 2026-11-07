package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

/** Where does each step run? Reactor stays on whatever thread delivered the last signal. */
public class ThreadTourDemo {
    static void where(String step) {
        System.out.printf("  %-26s on %s%n", step, Thread.currentThread().getName());
    }

    public static void main(String[] args) {
        System.out.println("1. no scheduler anywhere");
        Flux.range(1, 2)
                .doOnNext(i -> where("source emits " + i))
                .map(i -> i * 10)
                .subscribe(i -> where("subscriber gets " + i));

        System.out.println("2. after a timer (Mono.delay)");
        Mono.delay(Duration.ofMillis(10))
                .doOnNext(t -> where("timer fires"))
                .map(t -> "ok")
                .doOnNext(v -> where("map after the timer"))
                .block();

        System.out.println("3. flatMap over three timers");
        Flux.range(1, 3)
                .flatMap(i -> Mono.delay(Duration.ofMillis(10L * i)).thenReturn(i))
                .doOnNext(i -> where("downstream gets " + i))
                .blockLast();
    }
}
