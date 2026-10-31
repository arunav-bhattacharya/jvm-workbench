package workbench.reactive.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

public class PaymentLookup {
    private final IssuerApi api;

    public PaymentLookup(IssuerApi api) {
        this.api = api;
    }

    public Mono<String> status(String paymentId) {
        // fromCallable runs the lambda on every subscription. A thrown exception becomes onError,
        // and a null result becomes an empty Mono. (Lesson 6 moves this blocking call off the caller's thread.)
        return Mono.fromCallable(() -> api.fetchStatus(paymentId));
    }

    public Flux<String> statuses(List<String> paymentIds) {
        // map runs once per item, only when the subscriber requests that item
        return Flux.fromIterable(paymentIds).map(api::fetchStatus);
    }
}
