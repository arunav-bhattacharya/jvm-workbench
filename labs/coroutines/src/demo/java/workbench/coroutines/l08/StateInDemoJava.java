// Java equivalent of StateInDemo.kt with Reactor: replay(1).refCount(1, grace) shares one
// upstream between subscribers, starts it with the first one, and stops it when the last one
// has been gone for the grace period, like stateIn with WhileSubscribed(300).
package workbench.coroutines.l08;

import java.time.Duration;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;

public class StateInDemoJava {
    static long t0;
    static void at(String msg) { System.out.printf("%5d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, msg); }

    public static void main(String[] args) throws InterruptedException {
        t0 = System.nanoTime();
        // a cold flux that polls the FX provider every 100 ms
        Flux<Double> polls = Flux.interval(Duration.ZERO, Duration.ofMillis(100))
            .map(n -> 1.0800 + n / 10_000.0)
            .doOnSubscribe(s -> at("upstream: polling started"))
            .doOnCancel(() -> at("upstream: polling stopped"));

        Flux<Double> rate = polls.replay(1).refCount(1, Duration.ofMillis(300));
        at("refCount returned; waiting 200 ms before the first dashboard");
        Thread.sleep(200);

        Disposable a = rate.subscribe();
        Disposable b = rate.subscribe();
        at("two dashboards subscribed");
        Thread.sleep(250);
        a.dispose();
        b.dispose();
        at("both dashboards left");
        Thread.sleep(500);
        at("done");
    }
}
