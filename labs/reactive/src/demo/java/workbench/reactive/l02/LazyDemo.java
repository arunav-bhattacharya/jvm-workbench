package workbench.reactive.l02;

import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

/** Mono.just, fromCallable and defer, each subscribed twice. Count the calls. */
public class LazyDemo {
    static final AtomicInteger calls = new AtomicInteger();

    static String fetchFxRate() {
        calls.incrementAndGet();
        return "EURUSD=1.08";
    }

    public static void main(String[] args) {
        run("just", () -> Mono.just(fetchFxRate()));
        run("fromCallable", () -> Mono.fromCallable(LazyDemo::fetchFxRate));
        run("defer", () -> Mono.defer(() -> Mono.just(fetchFxRate())));
    }

    static void run(String name, java.util.function.Supplier<Mono<String>> build) {
        calls.set(0);
        Mono<String> rate = build.get();
        int atAssembly = calls.get();
        rate.block();
        rate.block();
        System.out.printf("%-13s calls at assembly: %d, after 2 subscriptions: %d%n", name, atAssembly, calls.get());
    }
}
