package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

/**
 * Four belts in the bakery's program, four backpressure decisions. Each method is one operator.
 * Decide which one before you type: does the source honour request(n)? May anything be lost?
 */
public final class BeltPolicies {
    private BeltPolicies() {
    }

    /**
     * The nightly report reads the day's order rows from the order book's database, which fetches as many
     * rows as it is asked for. The report writer downstream asks for everything at once. Keep every row,
     * but never ask the database for more than 100 rows at a time.
     */
    public static <T> Flux<T> nightlyReport(Flux<T> orderRows) {
        throw new UnsupportedOperationException("TODO: cap each upstream request at 100");
    }

    /**
     * The oven thermometer sends readings whether anyone asks or not. The screen is slow and only ever needs
     * the newest reading: when it asks for one, give it the most recent reading and forget the older ones.
     */
    public static <T> Flux<T> latestTemperature(Flux<T> readings) {
        throw new UnsupportedOperationException("TODO: keep only the newest reading");
    }

    /**
     * Orders from the website arrive when customers click, and the source cannot slow down. None may be lost
     * silently. Hold up to 1,000 orders for a slow subscriber; if a 1,001st has to wait, fail the stream with an
     * overflow error (after the subscriber has received the 1,000 that were held) so the gap is visible.
     */
    public static <T> Flux<T> webOrders(Flux<T> orders) {
        throw new UnsupportedOperationException("TODO: bounded buffer, loud overflow");
    }

    /**
     * Books a courier van for every delivery. The courier's booking service allows 20 open requests per
     * customer; never have more than 20 calls in flight. The order of the results does not matter.
     */
    public static <T, R> Flux<R> bookCouriers(Flux<T> deliveries, Function<T, Mono<R>> courierCall) {
        throw new UnsupportedOperationException("TODO: at most 20 calls in flight");
    }
}
