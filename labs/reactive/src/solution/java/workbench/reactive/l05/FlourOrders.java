package workbench.reactive.l05;

import reactor.core.Exceptions;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.TimeoutException;

public class FlourOrders {
    private final Mill mill;

    public FlourOrders(Mill mill) {
        this.mill = mill;
    }

    public Mono<String> place(String orderId) {
        return Mono.defer(() -> mill.order(orderId))                 // 1. a fresh call to the mill on every (re)subscription
                .timeout(Duration.ofMillis(500))                       // 2. per attempt, because it sits inside the retry
                .retryWhen(Retry.backoff(3, Duration.ofMillis(100))    // 3. 100, 200, 400 ms between attempts
                        .jitter(0)                                     //    no jitter, so tests can check exact times
                        .filter(FlourOrders::worthRetrying))           // 4. a refusal goes straight through
                .onErrorResume(Exceptions::isRetryExhausted,           // 5. out of retries: mark it pending, don't fail
                        e -> Mono.just("PENDING:" + orderId));
    }

    private static boolean worthRetrying(Throwable e) {
        return e instanceof MillBusyException || e instanceof TimeoutException;
    }
}
