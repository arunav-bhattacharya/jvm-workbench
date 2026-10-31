package workbench.reactive.l05;

import reactor.core.Exceptions;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.TimeoutException;

public class ResilientAuthorizer {
    private final CardIssuer issuer;

    public ResilientAuthorizer(CardIssuer issuer) {
        this.issuer = issuer;
    }

    public Mono<String> authorize(String paymentId) {
        return Mono.defer(() -> issuer.authorize(paymentId))       // 1. a fresh issuer call on every (re)subscription
                .timeout(Duration.ofMillis(500))                     // 2. per attempt, because it sits inside the retry
                .retryWhen(Retry.backoff(3, Duration.ofMillis(100))  // 3. 100, 200, 400 ms between attempts
                        .jitter(0)                                   //    no jitter, so tests can check exact times
                        .filter(ResilientAuthorizer::worthRetrying)) // 4. declines go straight through
                .onErrorResume(Exceptions::isRetryExhausted,         // 5. out of retries: park it, don't fail
                        e -> Mono.just("PENDING:" + paymentId));
    }

    private static boolean worthRetrying(Throwable e) {
        return e instanceof IssuerUnavailableException || e instanceof TimeoutException;
    }
}
