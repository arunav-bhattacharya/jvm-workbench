package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;

/** 200 settlement calls against a bank that allows 20 open requests per client. */
public class RateLimitDemo {
    static final Semaphore openRequests = new Semaphore(20);
    static final AtomicInteger refused = new AtomicInteger();

    // the bank: 50 ms per call, and a 21st concurrent request is refused with a 429
    static Mono<String> bankCall(int id) {
        return Mono.defer(() -> {
            if (!openRequests.tryAcquire()) {
                refused.incrementAndGet();
                return Mono.error(new IllegalStateException("429 Too Many Requests"));
            }
            return Mono.delay(Duration.ofMillis(50)).map(tick -> {
                openRequests.release();                         // the response frees the slot
                return "receipt-" + id;
            });
        });
    }

    static void run(String title, Function<Flux<Integer>, Flux<String>> settle) {
        refused.set(0);
        long t0 = System.nanoTime();
        long settled = settle.apply(Flux.range(1, 200)).count().block();
        System.out.printf("%-22s %3d settled, %3d refused with 429, in %3d ms%n",
                title, settled, refused.get(), (System.nanoTime() - t0) / 1_000_000);
    }

    public static void main(String[] args) {
        bankCall(0).block();                                    // warm-up, so the timings below are fair
        // a refused call is skipped, so one 429 doesn't end the whole batch (lesson 5 of this track)
        run("1. flatMap(call)", f -> f.flatMap(id -> bankCall(id).onErrorResume(e -> Mono.empty())));
        run("2. flatMap(call, 20)", f -> f.flatMap(id -> bankCall(id).onErrorResume(e -> Mono.empty()), 20));
    }
}
