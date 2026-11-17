package workbench.flows.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

// Closest Java equivalent of flatMapMerge(2): Reactor's flatMap with concurrency 2.
// Real time, so the printed times drift by a few ms; the rounded column is the model.
public class BurnersJava {
    static final Map<String, Long> COOKING_MS = new LinkedHashMap<>();
    static {
        COOKING_MS.put("soup", 300L); COOKING_MS.put("salad", 100L); COOKING_MS.put("roast", 200L);
        COOKING_MS.put("bread", 50L); COOKING_MS.put("pie", 150L);
    }
    static final AtomicInteger onBurners = new AtomicInteger();
    static final AtomicInteger mostOnBurners = new AtomicInteger();
    static long t0;

    static boolean quiet;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %3d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static void started(String dish) {
        mostOnBurners.accumulateAndGet(onBurners.incrementAndGet(), Math::max);
        log("    start cooking " + dish + " (on the burners: " + onBurners.get() + ")");
    }

    // non-blocking cooking: the wait happens inside the returned Mono
    static Mono<String> cook(String dish) {
        return Mono.delay(Duration.ofMillis(COOKING_MS.get(dish)))
                .doOnSubscribe(s -> started(dish))
                .doOnNext(tick -> onBurners.decrementAndGet())    // the dish is done
                .thenReturn(dish + ":plate");
    }

    // blocking cooking, called in the mapper: the wait happens before flatMap gets a publisher
    static String cookNow(String dish) {
        started(dish);
        try { Thread.sleep(COOKING_MS.get(dish)); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        onBurners.decrementAndGet();
        return dish + ":plate";
    }

    static void scenario(String title, Flux<String> plates) {
        if (!quiet) System.out.println("== " + title);
        mostOnBurners.set(0);
        t0 = System.nanoTime();
        plates.doOnNext(p -> log("subscriber got " + p)).blockLast();
        log("done, most on the burners = " + mostOnBurners.get());
    }

    public static void main(String[] args) {
        for (boolean warmUp : new boolean[] {true, false}) {   // a silent first round loads the classes
            quiet = warmUp;
            run();
        }
    }

    static void run() {
        scenario("flatMap(cook, 2): the wait is inside the returned Mono",
                Flux.fromIterable(COOKING_MS.keySet()).flatMap(BurnersJava::cook, 2));
        scenario("flatMap(d -> Mono.just(cookNow(d)), 2): the wait is in the mapper",
                Flux.fromIterable(COOKING_MS.keySet()).flatMap(d -> Mono.just(cookNow(d)), 2));
    }
}
