package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Eight blocking stock-book calls of 100 ms each. Where you put subscribeOn decides how long they take. */
public class BlockingCallDemo {
    static final Set<Thread> threads = ConcurrentHashMap.newKeySet();

    // a call through a blocking database driver: it holds the calling thread for 100 ms
    static int loavesLeft(String shop) {
        threads.add(Thread.currentThread());
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return 10;
    }

    static void run(String title, Flux<Integer> counts) {
        threads.clear();
        long t0 = System.nanoTime();
        long n = counts.count().block();
        Thread one = threads.iterator().next();
        System.out.printf("%-34s %d calls in %3d ms on %d thread(s), e.g. %s (virtual=%s)%n", title, n,
                (System.nanoTime() - t0) / 1_000_000, threads.size(), one.getName(), one.isVirtual());
    }

    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("virtual")) {
            // must be set before Reactor's Schedulers class is first used; normally a -D JVM flag
            System.setProperty("reactor.schedulers.defaultBoundedElasticOnVirtualThreads", "true");
        }
        List<String> shops = List.of("shop-1", "shop-2", "shop-3", "shop-4", "shop-5", "shop-6", "shop-7", "shop-8");

        run("1. fromCallable, no scheduler", Flux.fromIterable(shops)
                .flatMap(s -> Mono.fromCallable(() -> loavesLeft(s))));

        run("2. subscribeOn on the outer Flux", Flux.fromIterable(shops)
                .flatMap(s -> Mono.fromCallable(() -> loavesLeft(s)))
                .subscribeOn(Schedulers.boundedElastic()));

        run("3. subscribeOn on each call", Flux.fromIterable(shops)
                .flatMap(s -> Mono.fromCallable(() -> loavesLeft(s))
                        .subscribeOn(Schedulers.boundedElastic())));
    }
}
