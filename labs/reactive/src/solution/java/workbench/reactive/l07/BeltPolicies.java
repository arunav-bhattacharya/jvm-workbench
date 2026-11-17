package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

public final class BeltPolicies {
    private BeltPolicies() {
    }

    public static <T> Flux<T> nightlyReport(Flux<T> orderRows) {
        // turns one huge request from downstream into requests of 100, then 75 each time 75 have gone out
        return orderRows.limitRate(100);
    }

    public static <T> Flux<T> latestTemperature(Flux<T> readings) {
        // requests unbounded from the thermometer and keeps one slot: the newest reading wins
        return readings.onBackpressureLatest();
    }

    public static <T> Flux<T> webOrders(Flux<T> orders) {
        // holds up to 1,000; the next one cancels the source and ends the stream with an
        // OverflowException, delivered after the subscriber drains the buffer
        return orders.onBackpressureBuffer(1_000);
    }

    public static <T, R> Flux<R> bookCouriers(Flux<T> deliveries, Function<T, Mono<R>> courierCall) {
        // flatMap subscribes to at most 20 inner calls, and asks the source for a new delivery
        // only when one of them finishes
        return deliveries.flatMap(courierCall, 20);
    }
}
