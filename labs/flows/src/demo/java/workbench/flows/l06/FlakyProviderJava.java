package workbench.flows.l06;

import reactor.core.Exceptions;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

// Closest Java equivalent of the flaky-provider pattern: Reactor's timeout, retryWhen(Retry.backoff) and
// onErrorResume. Case B: the primary always takes 1000 ms. Real time, so expect a few ms of drift.
public class FlakyProviderJava {
    static long t0;
    static boolean quiet;
    static final AtomicInteger primaryCalls = new AtomicInteger();

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %4d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static Mono<String> primary() {
        return Mono.defer(() -> {
            log("    primary call " + primaryCalls.incrementAndGet() + " starts");
            return Mono.delay(Duration.ofMillis(1_000)).thenReturn("USD/EUR 0.92 from primary");
        });
    }

    static Mono<String> fallback() {
        return Mono.defer(() -> {
            log("    fallback call starts");
            return Mono.delay(Duration.ofMillis(30)).thenReturn("USD/EUR 0.92 from fallback");
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
        primaryCalls.set(0);
        t0 = System.nanoTime();
        String rate = primary()
                .timeout(Duration.ofMillis(300))                                                   // per attempt
                .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0).filter(FlakyProviderJava::transientError))
                .onErrorResume(e -> Exceptions.isRetryExhausted(e) || transientError(e), e -> {
                    log("    primary gave up: " + e.getMessage() + " (cause: " + e.getCause().getClass().getSimpleName() + ")");
                    return fallback();
                })
                .block();
        log("  result: " + rate + "  (primary calls " + primaryCalls.get() + ")");
    }
}
