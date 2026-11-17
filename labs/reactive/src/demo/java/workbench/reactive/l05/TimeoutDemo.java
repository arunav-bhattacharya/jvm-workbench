package workbench.reactive.l05;

import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

/** timeout turns silence into an error you can handle. Where you put it decides what it limits. */
public class TimeoutDemo {
    public static void main(String[] args) {
        Mono<String> slowPrice = Mono.delay(Duration.ofMillis(300)).thenReturn("fresh flour price 0.92")
                .doOnCancel(() -> System.out.println("  slow call cancelled"));

        try {
            slowPrice.timeout(Duration.ofMillis(100)).block();
        } catch (RuntimeException e) {
            System.out.println("timeout: " + e.getCause());
        }

        String price = slowPrice.timeout(Duration.ofMillis(100))
                .onErrorResume(TimeoutException.class, e -> Mono.just("yesterday's price 0.90"))
                .block();
        System.out.println("with fallback: " + price);

        AtomicInteger attempts = new AtomicInteger();
        long t0 = System.nanoTime();
        try {
            String r = Mono.defer(() -> { attempts.incrementAndGet(); return slowPrice; })
                    .timeout(Duration.ofMillis(100))                        // per attempt
                    .retryWhen(Retry.backoff(5, Duration.ofMillis(50)).jitter(0))
                    .timeout(Duration.ofMillis(400))                        // budget for the whole call
                    .block();
            System.out.printf("budget: got %s after %d attempts and %d ms%n",
                    r, attempts.get(), (System.nanoTime() - t0) / 1_000_000);
        } catch (RuntimeException e) {
            System.out.printf("budget: gave up after %d attempts and %d ms: %s%n",
                    attempts.get(), (System.nanoTime() - t0) / 1_000_000, e.getCause().getClass().getSimpleName());
        }
    }
}
