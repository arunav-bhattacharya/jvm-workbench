package workbench.flows.l06;

import reactor.core.Exceptions;
import reactor.core.publisher.Flux;
import reactor.util.retry.Retry;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

// Closest Java equivalent: Reactor's retry re-subscribes, so a cold Flux replays from the top too.
public class RetryReplayJava {
    static long t0;
    static boolean quiet;

    public static void main(String[] args) {
        System.out.println("== the delivery note: the reader loses the connection after line 2 on the first attempt; retry(3)");
        AtomicInteger attempt = new AtomicInteger();
        Flux<String> feed = Flux.defer(() -> {
            int n = attempt.incrementAndGet();
            return n == 1
                    ? Flux.concat(Flux.just("flour", "eggs"), Flux.error(new IOException("reader lost the connection")))
                    : Flux.just("flour", "eggs", "butter");
        });
        System.out.println("  the pantry received " + feed.retry(3).collectList().block());

        System.out.println("== Retry.backoff(3, 100 ms) with jitter off, on a call that always fails (real time)");
        quiet = true;
        backoff();          // a silent first round loads the classes, so the timings below are clean
        quiet = false;
        backoff();
    }

    static void backoff() {
        AtomicInteger calls = new AtomicInteger();
        Flux<String> bakery = Flux.defer(() -> {
            long ms = (System.nanoTime() - t0) / 1_000_000;
            String line = String.format("  call %d at about %d ms", calls.incrementAndGet(), Math.round(ms / 50.0) * 50);
            if (!quiet) System.out.println(line);
            return Flux.error(new IOException("line dropped"));
        });
        t0 = System.nanoTime();
        try {
            bakery.retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0)).blockLast();
        } catch (RuntimeException e) {
            if (!quiet) System.out.println("  caller saw " + e.getClass().getSimpleName() + ": " + e.getMessage()
                    + "; isRetryExhausted=" + Exceptions.isRetryExhausted(e) + "; cause: " + e.getCause());
        }
    }
}
