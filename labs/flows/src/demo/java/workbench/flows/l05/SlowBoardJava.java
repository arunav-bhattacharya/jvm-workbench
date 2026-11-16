package workbench.flows.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

// Closest Java equivalent: Reactor's combineLatest in front of a dashboard that needs 100 ms
// per update and asks for one at a time. Real time; the rounded column is the model.
public class SlowBoardJava {
    static long t0;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("%5d ms (about %4d)  %s%n", ms, Math.round(ms / 10.0) * 10, msg);
    }

    static Flux<String> board() {
        Flux<Long> ticks = Flux.interval(Duration.ofMillis(10)).map(i -> i + 1).take(10);
        return Flux.combineLatest(ticks, Flux.just("cfg"), (i, c) -> i + "/" + c);
    }

    public static void main(String[] args) {
        board().then().block();      // warm up, output ignored
        System.out.println("== Flux.combineLatest, slow subscriber");
        t0 = System.nanoTime();
        board().concatMap(v -> Mono.delay(Duration.ofMillis(100)).thenReturn(v), 1)
                .doOnNext(v -> log("-> " + v))
                .blockLast();
        log("done");
    }
}
