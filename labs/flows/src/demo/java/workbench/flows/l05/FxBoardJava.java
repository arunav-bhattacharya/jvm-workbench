package workbench.flows.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

// Closest Java equivalent: Reactor's zip and combineLatest on the same price and FX feeds.
// Real time; the rounded column is the model.
public class FxBoardJava {
    static long t0;

    static boolean quiet;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %3d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static Flux<Integer> prices() {
        return Flux.just(1000, 1010, 1020, 1030, 1040, 1050)
                .delayElements(Duration.ofMillis(100))
                .doOnNext(p -> log("price  " + p));
    }

    static Flux<Double> fxRates() {
        return Flux.concat(Mono.delay(Duration.ofMillis(250)).thenReturn(0.92),
                        Mono.delay(Duration.ofMillis(300)).thenReturn(0.95))
                .doOnNext(fx -> log("fx     " + fx));
    }

    public static void main(String[] args) {
        for (boolean warmUp : new boolean[] {true, false}) {   // a silent first round loads the classes
            quiet = warmUp;
            run();
        }
    }

    static void run() {
        if (!quiet) System.out.println("== Flux.zip: pairs by index");
        t0 = System.nanoTime();
        Flux.zip(prices(), fxRates(), (p, fx) -> p + "@" + fx)
                .doOnNext(s -> log("  -> " + s))
                .blockLast();
        if (!quiet) System.out.println("== Flux.combineLatest: the latest of each");
        t0 = System.nanoTime();
        Flux.combineLatest(prices(), fxRates(), (p, fx) -> p + "@" + fx)
                .doOnNext(s -> log("  -> " + s))
                .blockLast();
    }
}
