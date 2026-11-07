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
        Mono<String> northbank = ask("northbank", 120, "1.0845");
        Mono<String> eastgate = ask("eastgate", 300, "1.0841");
        Mono<String> fjord = ask("fjord", 200, "1.0843");
        Duration deadline = Duration.ofMillis(250);

        long t0 = System.nanoTime();
        List<String> inTurn = Flux.concat(northbank, eastgate, fjord).collectList().block();
        System.out.printf("one after another:     %d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, inTurn);

        t0 = System.nanoTime();
        var atOnce = Mono.zip(northbank, eastgate, fjord).block();
        System.out.printf("Mono.zip, all at once: %d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, atOnce);

        t0 = System.nanoTime();
        var withDeadline = Mono.zip(inTime(northbank, deadline), inTime(eastgate, deadline), inTime(fjord, deadline)).block();
        System.out.printf("with a 250 ms deadline: %d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, withDeadline);
    }
}
