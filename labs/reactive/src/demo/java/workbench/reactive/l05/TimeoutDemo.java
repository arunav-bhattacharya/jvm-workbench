package workbench.reactive.l05;

import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

/** timeout turns silence into an error you can handle. Where you put it decides what it limits. */
public class TimeoutDemo {
    public static void main(String[] args) {
        Mono<String> slowRate = Mono.delay(Duration.ofMillis(300)).thenReturn("live rate 1.08")
                .doOnCancel(() -> System.out.println("  slow call cancelled"));

        try {
            slowRate.timeout(Duration.ofMillis(100)).block();
        } catch (RuntimeException e) {
            System.out.println("timeout: " + e.getCause());
        }

        String rate = slowRate.timeout(Duration.ofMillis(100))
                .onErrorResume(TimeoutException.class, e -> Mono.just("cached rate 1.07"))
                .block();
        System.out.println("with fallback: " + rate);

        AtomicInteger attempts = new AtomicInteger();
        long t0 = System.nanoTime();
        try {
            Mono.defer(() -> { attempts.incrementAndGet(); return slowRate; })
                    .timeout(Duration.ofMillis(100))                        // per attempt
                    .retryWhen(Retry.backoff(5, Duration.ofMillis(50)).jitter(0))
                    .timeout(Duration.ofMillis(400))                        // budget for the whole call
                    .block();
        } catch (RuntimeException e) {
            System.out.printf("budget: gave up after %d attempts and %d ms: %s%n",
                    attempts.get(), (System.nanoTime() - t0) / 1_000_000, e.getCause().getClass().getSimpleName());
        }
    }
}
