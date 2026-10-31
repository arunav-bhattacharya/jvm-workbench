package workbench.reactive.l05;

import reactor.core.publisher.Mono;

/** The card issuer's authorization API. */
public interface CardIssuer {
    /**
     * Asks the issuer to authorize a payment. The Mono emits an authorization code, or fails with
     * {@link IssuerUnavailableException} (worth retrying) or {@link CardDeclinedException} (final).
     */
    Mono<String> authorize(String paymentId);
}
