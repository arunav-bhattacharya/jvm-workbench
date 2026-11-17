package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;

/** 200 delivery bookings against a courier service that allows 20 open requests per customer. */
public class CourierLimitDemo {
    static final Semaphore openRequests = new Semaphore(20);
    static final AtomicInteger refused = new AtomicInteger();

    // the courier: 50 ms per booking, and a 21st open request is refused
    static Mono<String> courierCall(int id) {
        return Mono.defer(() -> {
            if (!openRequests.tryAcquire()) {
                refused.incrementAndGet();
                return Mono.error(new IllegalStateException("too many open requests"));
            }
            return Mono.delay(Duration.ofMillis(50)).map(tick -> {
                openRequests.release();                         // the answer frees the slot
                return "van-" + id;
            });
        });
    }

    static void run(String title, Function<Flux<Integer>, Flux<String>> book) {
        refused.set(0);
        long t0 = System.nanoTime();
        long booked = book.apply(Flux.range(1, 200)).count().block();
        System.out.printf("%-22s %3d booked, %3d refused, in %3d ms%n",
                title, booked, refused.get(), (System.nanoTime() - t0) / 1_000_000);
    }

    public static void main(String[] args) {
        courierCall(0).block();                                    // warm-up, so the timings below are fair
        // a refused call is skipped, so one refusal doesn't end the whole batch (lesson 5 of this track)
        run("1. flatMap(call)", f -> f.flatMap(id -> courierCall(id).onErrorResume(e -> Mono.empty())));
        run("2. flatMap(call, 20)", f -> f.flatMap(id -> courierCall(id).onErrorResume(e -> Mono.empty()), 20));
    }
}
