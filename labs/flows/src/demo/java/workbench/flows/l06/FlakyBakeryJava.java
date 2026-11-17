package workbench.flows.l06;

import reactor.core.Exceptions;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

// Closest Java equivalent of the flaky-bakery pattern: Reactor's timeout, retryWhen(Retry.backoff) and
// onErrorResume. Case B: the corner bakery always takes 1000 ms. Real time, so expect a few ms of drift.
public class FlakyBakeryJava {
    static long t0;
    static boolean quiet;
    static final AtomicInteger cornerCalls = new AtomicInteger();

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %4d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static Mono<String> corner() {
        return Mono.defer(() -> {
            log("    corner call " + cornerCalls.incrementAndGet() + " starts");
            return Mono.delay(Duration.ofMillis(1_000)).thenReturn("sourdough from corner");
        });
    }

    static Mono<String> backup() {
        return Mono.defer(() -> {
            log("    backup call starts");
            return Mono.delay(Duration.ofMillis(30)).thenReturn("sourdough from backup");
        });
    }

    static boolean transientError(Throwable e) {
        return e instanceof IOException || e instanceof TimeoutException;
    }

    public static void main(String[] args) {
        quiet = true;
        run();              // a silent first round loads the classes, so the timings below are clean
        quiet = false;
        run();
    }

    static void run() {
        cornerCalls.set(0);
        t0 = System.nanoTime();
        String loaf = corner()
                .timeout(Duration.ofMillis(300))                                                   // per attempt
                .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0).filter(FlakyBakeryJava::transientError))
                .onErrorResume(e -> Exceptions.isRetryExhausted(e) || transientError(e), e -> {
                    log("    the corner bakery gave up: " + e.getMessage() + " (cause: " + e.getCause().getClass().getSimpleName() + ")");
                    return backup();
                })
                .block();
        log("  result: " + loaf + "  (corner calls " + cornerCalls.get() + ")");
    }
}
