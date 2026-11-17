package workbench.reactive.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

public class OrderLookup {
    private final OrderBook book;

    public OrderLookup(OrderBook book) {
        this.book = book;
    }

    public Mono<String> status(String orderId) {
        // fromCallable runs the lambda on every subscription. A thrown exception becomes onError,
        // and a null result becomes an empty Mono. (Lesson 6 moves this blocking call off the caller's thread.)
        return Mono.fromCallable(() -> book.fetchStatus(orderId));
    }

    public Flux<String> statuses(List<String> orderIds) {
        // map runs once per item, only when the subscriber requests that item
        return Flux.fromIterable(orderIds).map(book::fetchStatus);
    }
}
