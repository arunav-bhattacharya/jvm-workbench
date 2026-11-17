package workbench.flows.l07;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;

// Java equivalent: Reactor's replay(1).refCount(1, grace), on the REAL clock.
// Reactor's virtual clock lives in reactor-test, so this run is the Kotlin timeline
// scaled down ten times: a reading every 100 ms and a 500 ms grace period.
// Times vary by a few ms between runs.
public class SharingTimelineJava {

    static long t0;

    static void log(String what) {
        if (t0 == 0) t0 = System.nanoTime();   // the clock starts at the first upstream START
        System.out.printf("  t=%4d ms: %s%n", (System.nanoTime() - t0) / 1_000_000, what);
    }

    static Disposable open(Flux<Integer> reading) {
        return reading.subscribe(v -> log("A got " + v));
    }

    public static void main(String[] args) throws InterruptedException {
        AtomicInteger starts = new AtomicInteger();
        Flux<Integer> thermometer = Flux.defer(() -> {
            int run = starts.incrementAndGet();
            log("upstream START #" + run);
            return Flux.interval(Duration.ZERO, Duration.ofMillis(100))
                    .map(i -> run * 100 + i.intValue())
                    .doOnCancel(() -> log("upstream STOP #" + run));
        });
        Flux<Integer> reading = thermometer.replay(1).refCount(1, Duration.ofMillis(500));

        Disposable a = open(reading);
        Thread.sleep(250); a.dispose(); log("A leaves");
        Thread.sleep(150); log("A comes back"); a = open(reading);
        Thread.sleep(200); a.dispose(); log("A leaves");
        Thread.sleep(800); log("A comes back"); a = open(reading);
        Thread.sleep(150); a.dispose(); log("end, upstream starts=" + starts.get());
    }
}
