package workbench.flows.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.function.Function;

// Closest Java equivalent: Reactor's concatMap, flatMap and switchMap on the same timeline.
// Real time; the rounded column is the model.
public class FlatMapTrioJava {
    static long t0;

    static boolean quiet;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %3d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static Flux<Integer> picks() {
        return Flux.concat(Mono.just(1),
                        Mono.delay(Duration.ofMillis(100)).thenReturn(2),
                        Mono.delay(Duration.ofMillis(100)).thenReturn(3))
                .doOnNext(n -> log("outer emits " + n));
    }

    static Flux<String> details(int n) {
        return Flux.concat(Mono.delay(Duration.ofMillis(50)).thenReturn(n + "-a"),
                        Mono.delay(Duration.ofMillis(150)).thenReturn(n + "-b"))
                .doOnCancel(() -> log("  inner " + n + " cancelled"));
    }

    static void timeline(String name, Function<Flux<Integer>, Flux<String>> op) {
        if (!quiet) System.out.println("== " + name);
        t0 = System.nanoTime();
        op.apply(picks()).doOnNext(s -> log("    subscriber got " + s)).blockLast();
        log("done");
    }

    public static void main(String[] args) {
        for (boolean warmUp : new boolean[] {true, false}) {   // a silent first round loads the classes
            quiet = warmUp;
            run();
        }
    }

    static void run() {
        timeline("concatMap", f -> f.concatMap(FlatMapTrioJava::details));
        timeline("flatMap", f -> f.flatMap(FlatMapTrioJava::details));
        timeline("switchMap", f -> f.switchMap(FlatMapTrioJava::details));
    }
}
