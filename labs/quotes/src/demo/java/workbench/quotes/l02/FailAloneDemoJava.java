// Java equivalent with Reactor: a failed source fails Mono.zip unless each source handles its own error
package workbench.quotes.l02;

import reactor.core.publisher.Mono;

import java.io.IOException;
import java.time.Duration;
import java.util.Optional;

/** The same three calls zipped two ways: who survives a failure, and who survives a timeout? Real time. */
public class FailAloneDemoJava {
    static final Mono<String> northbank = Mono.delay(Duration.ofMillis(50)).then(Mono.error(new IOException("northbank 503")));
    static final Mono<String> fjord = Mono.delay(Duration.ofMillis(1_000)).thenReturn("fjord 1.0843")
            .timeout(Duration.ofMillis(100));                       // fjord's own client gives up at 100 ms
    static final Mono<String> eastgate = Mono.delay(Duration.ofMillis(300)).thenReturn("eastgate 1.0841");

    static Mono<Optional<String>> alone(Mono<String> call) {
        return call.map(Optional::of).onErrorResume(e -> Mono.just(Optional.empty()));
    }

    static void attempt(String what, Mono<?> zipped) {
        long t0 = System.nanoTime();
        String outcome;
        try {
            outcome = "answers " + zipped.block();
        } catch (RuntimeException e) {
            Throwable cause = e.getCause() != null ? e.getCause() : e;
            outcome = "failed: " + cause.getClass().getSimpleName() + ": " + cause.getMessage();
        }
        System.out.printf("%-34s at %3d ms  %s%n", what, (System.nanoTime() - t0) / 1_000_000, outcome);
    }

    public static void main(String[] args) {
        attempt("Mono.zip of the raw calls", Mono.zip(northbank, fjord, eastgate));
        attempt("Mono.zip, each call onErrorResume", Mono.zip(alone(northbank), alone(fjord), alone(eastgate)));
    }
}
