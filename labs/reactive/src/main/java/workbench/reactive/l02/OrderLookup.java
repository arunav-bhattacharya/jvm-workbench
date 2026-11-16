package workbench.reactive.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

/**
 * Looks up the status of cake orders in the bakery's order book.
 *
 * <p>Both methods are eager: they call the order book while the pipeline is being built, before
 * anyone subscribes, and only once no matter how many subscribers there are. Make them lazy:
 * <ul>
 *   <li>building the Mono or Flux must not call the order book,</li>
 *   <li>every subscription must make its own calls,</li>
 *   <li>an order book exception must arrive as {@code onError}, not be thrown by the method,</li>
 *   <li>an unknown order (the order book returns null) must give an empty Mono,</li>
 *   <li>{@code statuses} must only call the order book for items the subscriber actually requests.</li>
 * </ul>
 */
public class OrderLookup {
    private final OrderBook book;

    public OrderLookup(OrderBook book) {
        this.book = book;
    }

    public Mono<String> status(String orderId) {
        return Mono.just(book.fetchStatus(orderId));            // the call happens right here, once
    }

    public Flux<String> statuses(List<String> orderIds) {
        List<String> all = orderIds.stream().map(book::fetchStatus).toList();   // every call, right now
        return Flux.fromIterable(all);
    }
}
