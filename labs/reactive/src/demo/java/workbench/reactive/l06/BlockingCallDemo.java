package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.math.BigDecimal;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Eight blocking ledger calls of 100 ms each. Where you put subscribeOn decides how long they take. */
public class BlockingCallDemo {
    static final Set<Thread> threads = ConcurrentHashMap.newKeySet();

    // a JDBC-style call: it holds the calling thread for 100 ms
    static BigDecimal balance(String account) {
        threads.add(Thread.currentThread());
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return BigDecimal.TEN;
    }

    static void run(String title, Flux<BigDecimal> balances) {
        threads.clear();
        long t0 = System.nanoTime();
        long n = balances.count().block();
        Thread one = threads.iterator().next();
        System.out.printf("%-34s %d calls in %3d ms on %d thread(s), e.g. %s (virtual=%s)%n", title, n,
                (System.nanoTime() - t0) / 1_000_000, threads.size(), one.getName(), one.isVirtual());
    }

    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("virtual")) {
            // must be set before Reactor's Schedulers class is first used; normally a -D JVM flag
            System.setProperty("reactor.schedulers.defaultBoundedElasticOnVirtualThreads", "true");
        }
        List<String> accounts = List.of("a-1", "a-2", "a-3", "a-4", "a-5", "a-6", "a-7", "a-8");

        run("1. fromCallable, no scheduler", Flux.fromIterable(accounts)
                .flatMap(a -> Mono.fromCallable(() -> balance(a))));

        run("2. subscribeOn on the outer Flux", Flux.fromIterable(accounts)
                .flatMap(a -> Mono.fromCallable(() -> balance(a)))
                .subscribeOn(Schedulers.boundedElastic()));

        run("3. subscribeOn on each call", Flux.fromIterable(accounts)
                .flatMap(a -> Mono.fromCallable(() -> balance(a))
                        .subscribeOn(Schedulers.boundedElastic())));
    }
}
