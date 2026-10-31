package workbench.reactive.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

/**
 * Looks up payment statuses at the card issuer.
 *
 * <p>Both methods are eager: they call the issuer while the pipeline is being built, before
 * anyone subscribes, and only once no matter how many subscribers there are. Make them lazy:
 * <ul>
 *   <li>building the Mono or Flux must not call the issuer,</li>
 *   <li>every subscription must make its own calls,</li>
 *   <li>an issuer exception must arrive as {@code onError}, not be thrown by the method,</li>
 *   <li>an unknown payment (the issuer returns null) must give an empty Mono,</li>
 *   <li>{@code statuses} must only call the issuer for items the subscriber actually requests.</li>
 * </ul>
 */
public class PaymentLookup {
    private final IssuerApi api;

    public PaymentLookup(IssuerApi api) {
        this.api = api;
    }

    public Mono<String> status(String paymentId) {
        return Mono.just(api.fetchStatus(paymentId));            // the call happens right here, once
    }

    public Flux<String> statuses(List<String> paymentIds) {
        List<String> all = paymentIds.stream().map(api::fetchStatus).toList();   // every call, right now
        return Flux.fromIterable(all);
    }
}
