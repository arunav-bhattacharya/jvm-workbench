package workbench.flows.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

// Closest Java equivalent of collectLatest: Reactor's switchMap. A new tick cancels the
// repricing in flight. Real time, so expect a few ms of drift.
public class LatestJoinJava {
    static long t0;
    static boolean quiet;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("t=%3d (about %3d) %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static void run() {
        t0 = System.nanoTime();
        Flux.range(1, 3)
                .delayElements(Duration.ofMillis(100))
                .doOnNext(tick -> log("emit " + tick))
                .switchMap(tick -> Mono.delay(Duration.ofMillis(300))
                        .doOnSubscribe(s -> log("start " + tick))
                        .doOnCancel(() -> log("cancelled " + tick))   // a signal: nothing waits for cleanup
                        .thenReturn(tick))
                .doOnNext(tick -> log("done " + tick))
                .blockLast();
    }

    public static void main(String[] args) {
        quiet = true;
        run();            // a silent first run loads the classes, so the timings below are clean
        quiet = false;
        run();
    }
}
