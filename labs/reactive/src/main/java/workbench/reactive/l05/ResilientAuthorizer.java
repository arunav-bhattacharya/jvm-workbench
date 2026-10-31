package workbench.reactive.l05;

import reactor.core.publisher.Mono;

/**
 * Wraps a flaky {@link CardIssuer} with a timeout, retries with backoff, and a fallback.
 *
 * <p>{@link #authorize} must:
 * <ol>
 *   <li>give each attempt 500 ms; an attempt that takes longer counts as failed,</li>
 *   <li>retry {@link IssuerUnavailableException} and timeouts up to 3 times, waiting 100 ms,
 *       then 200 ms, then 400 ms (exponential backoff, no jitter, so the tests can check times),</li>
 *   <li>call the issuer again for every attempt (the issuer picks its answer when called),</li>
 *   <li>never retry a {@link CardDeclinedException}: pass it straight to the caller,</li>
 *   <li>when all retries are used up, emit {@code "PENDING:" + paymentId} instead of failing,
 *       so the payment can be completed later.</li>
 * </ol>
 */
public class ResilientAuthorizer {
    private final CardIssuer issuer;

    public ResilientAuthorizer(CardIssuer issuer) {
        this.issuer = issuer;
    }

    public Mono<String> authorize(String paymentId) {
        throw new UnsupportedOperationException("TODO: timeout, retry with backoff, fallback");
    }
}
