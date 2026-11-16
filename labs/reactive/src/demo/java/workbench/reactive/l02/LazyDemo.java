package workbench.reactive.l02;

import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

/** Mono.just, fromCallable and defer, each subscribed twice. Count the calls. */
public class LazyDemo {
    static final AtomicInteger calls = new AtomicInteger();

    static String fetchFlourPrice() {
        calls.incrementAndGet();
        return "flour=1.20/kg";
    }

    public static void main(String[] args) {
        run("just", () -> Mono.just(fetchFlourPrice()));
        run("fromCallable", () -> Mono.fromCallable(LazyDemo::fetchFlourPrice));
        run("defer", () -> Mono.defer(() -> Mono.just(fetchFlourPrice())));
    }

    static void run(String name, java.util.function.Supplier<Mono<String>> build) {
        calls.set(0);
        Mono<String> price = build.get();
        int atAssembly = calls.get();
        price.block();
        price.block();
        System.out.printf("%-13s calls at assembly: %d, after 2 subscriptions: %d%n", name, atAssembly, calls.get());
    }
}
