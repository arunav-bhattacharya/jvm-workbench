package workbench.flows.l05;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

// Closest Java equivalent of flatMapMerge(2): Reactor's flatMap with concurrency 2.
// Real time, so the printed times drift by a few ms; the rounded column is the model.
public class FeeFanOutJava {
    static final Map<String, Long> LATENCY = new LinkedHashMap<>();
    static { LATENCY.put("m1", 300L); LATENCY.put("m2", 100L); LATENCY.put("m3", 200L); LATENCY.put("m4", 50L); LATENCY.put("m5", 150L); }
    static final AtomicInteger inFlight = new AtomicInteger();
    static final AtomicInteger maxInFlight = new AtomicInteger();
    static long t0;

    static boolean quiet;

    static void log(String msg) {
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String line = String.format("%5d ms (about %3d)  %s", ms, Math.round(ms / 50.0) * 50, msg);
        if (!quiet) System.out.println(line);
    }

    static void started(String m) {
        maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
        log("    start lookup " + m + " (in flight: " + inFlight.get() + ")");
    }

    // a non-blocking lookup: the wait happens inside the returned Mono
    static Mono<String> lookup(String m) {
        return Mono.delay(Duration.ofMillis(LATENCY.get(m)))
                .doOnSubscribe(s -> started(m))
                .doOnNext(tick -> inFlight.decrementAndGet())    // the wait is over
                .thenReturn(m + ":fee");
    }

    // a blocking lookup, called in the mapper: the wait happens before flatMap gets a publisher
    static String lookupNow(String m) {
        started(m);
        try { Thread.sleep(LATENCY.get(m)); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        inFlight.decrementAndGet();
        return m + ":fee";
    }

    static void scenario(String title, Flux<String> fees) {
        if (!quiet) System.out.println("== " + title);
        maxInFlight.set(0);
        t0 = System.nanoTime();
        fees.doOnNext(f -> log("subscriber got " + f)).blockLast();
        log("done, max in flight = " + maxInFlight.get());
    }

    public static void main(String[] args) {
        for (boolean warmUp : new boolean[] {true, false}) {   // a silent first round loads the classes
            quiet = warmUp;
            run();
        }
    }

    static void run() {
        scenario("flatMap(lookup, 2): the wait is inside the returned Mono",
                Flux.fromIterable(LATENCY.keySet()).flatMap(FeeFanOutJava::lookup, 2));
        scenario("flatMap(m -> Mono.just(lookupNow(m)), 2): the wait is in the mapper",
                Flux.fromIterable(LATENCY.keySet()).flatMap(m -> Mono.just(lookupNow(m)), 2));
    }
}
