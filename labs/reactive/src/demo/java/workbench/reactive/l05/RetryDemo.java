package workbench.reactive.l05;

import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

/** retry re-subscribes. What gets re-run depends on how the source was built. */
public class RetryDemo {
    static final AtomicInteger calls = new AtomicInteger();
    static long t0;

    // fails on the first two calls, succeeds on the third
    static String callIssuer() {
        int n = calls.incrementAndGet();
        System.out.printf("  [%3d ms] attempt %d%n", (System.nanoTime() - t0) / 1_000_000, n);
        if (n < 3) throw new IllegalStateException("issuer busy");
        return "APPROVED";
    }

    static String alwaysFails() {
        callIssuer();
        throw new IllegalStateException("issuer down");
    }

    // a client that calls the issuer when the method is called, and wraps the answer in a Mono
    static Mono<String> eagerClient() {
        try {
            return Mono.just(callIssuer());
        } catch (RuntimeException e) {
            return Mono.error(e);
        }
    }

    public static void main(String[] args) {
        // warm up Reactor and the formatter, so the first timings don't include class loading
        Mono.fromCallable(() -> 1).retryWhen(Retry.backoff(1, Duration.ofMillis(1))).block();
        String.format("%3d", 0);

        start("1. fromCallable + retryWhen(backoff 50 ms, no jitter)");
        System.out.println("  -> " + Mono.fromCallable(RetryDemo::callIssuer)
                .retryWhen(Retry.backoff(3, Duration.ofMillis(50)).jitter(0))
                .block());

        start("2. retry(2) on a source that always fails");
        try {
            Mono.fromCallable(RetryDemo::alwaysFails).retry(2).block();
        } catch (RuntimeException e) {
            System.out.println("  -> " + e);
        }

        start("3. backoff exhausted");
        try {
            Mono.fromCallable(RetryDemo::alwaysFails)
                    .retryWhen(Retry.backoff(3, Duration.ofMillis(50)).jitter(0))
                    .block();
        } catch (RuntimeException e) {
            System.out.println("  -> " + e + "\n     cause: " + e.getCause());
        }

        start("4. retry(3) on a Mono built from one eager call");
        AtomicInteger subscriptions = new AtomicInteger();
        try {
            eagerClient().doOnSubscribe(s -> subscriptions.incrementAndGet()).retry(3).block();
        } catch (RuntimeException e) {
            System.out.println("  -> " + e + " after " + subscriptions.get() + " subscriptions");
        }
    }

    static void start(String title) {
        System.out.println(title);
        calls.set(0);
        t0 = System.nanoTime();
    }
}
