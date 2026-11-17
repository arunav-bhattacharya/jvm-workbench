// Java equivalent with Reactor: concat runs the calls in turn, Mono.zip subscribes to all three at once
package workbench.quotes.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;
import java.util.Optional;

/** One quote from three providers: one after another, all at once, and all at once inside a deadline. Real time. */
public class FanOutDemoJava {
    static Mono<String> ask(String name, long ms, String price) {
        return Mono.delay(Duration.ofMillis(ms)).thenReturn(name + " " + price);
    }

    static Mono<Optional<String>> inTime(Mono<String> call, Duration deadline) {
        return call.timeout(deadline).map(Optional::of).onErrorResume(e -> Mono.just(Optional.empty()));
    }

    public static void main(String[] args) {
        Mono<String> northline = ask("northline", 120, "12.45");
        Mono<String> eastgate = ask("eastgate", 300, "12.41");
        Mono<String> fjord = ask("fjord", 200, "12.43");
        Duration deadline = Duration.ofMillis(250);

        long t0 = System.nanoTime();
        List<String> inTurn = Flux.concat(northline, eastgate, fjord).collectList().block();
        System.out.printf("one after another:     %d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, inTurn);

        t0 = System.nanoTime();
        var atOnce = Mono.zip(northline, eastgate, fjord).block();
        System.out.printf("Mono.zip, all at once: %d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, atOnce);

        t0 = System.nanoTime();
        var withDeadline = Mono.zip(inTime(northline, deadline), inTime(eastgate, deadline), inTime(fjord, deadline)).block();
        System.out.printf("with a 250 ms deadline: %d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, withDeadline);
    }
}
