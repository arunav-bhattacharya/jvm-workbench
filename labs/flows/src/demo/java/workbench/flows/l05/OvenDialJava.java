package workbench.flows.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

// Closest Java equivalent: Reactor's zip and combineLatest on the same thermometer and dial.
// Real time; the rounded column is the model.
public class OvenDialJava {
    static long t0;

    static boolean quiet;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %3d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static Flux<Integer> readings() {
        return Flux.just(150, 152, 154, 156, 158, 160)
                .delayElements(Duration.ofMillis(100))
                .doOnNext(c -> log("reading " + c));
    }

    static Flux<Integer> dial() {
        return Flux.concat(Mono.delay(Duration.ofMillis(250)).thenReturn(180),
                        Mono.delay(Duration.ofMillis(300)).thenReturn(200))
                .doOnNext(d -> log("dial    " + d));
    }

    public static void main(String[] args) {
        for (boolean warmUp : new boolean[] {true, false}) {   // a silent first round loads the classes
            quiet = warmUp;
            run();
        }
    }

    static void run() {
        if (!quiet) System.out.println("== Flux.zip: pairs by number");
        t0 = System.nanoTime();
        Flux.zip(readings(), dial(), (c, d) -> c + " of " + d)
                .doOnNext(s -> log("  screen shows " + s))
                .blockLast();
        if (!quiet) System.out.println("== Flux.combineLatest: the latest of each");
        t0 = System.nanoTime();
        Flux.combineLatest(readings(), dial(), (c, d) -> c + " of " + d)
                .doOnNext(s -> log("  screen shows " + s))
                .blockLast();
    }
}
