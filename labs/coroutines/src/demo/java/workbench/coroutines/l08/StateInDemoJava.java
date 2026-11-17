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
        // a cold flux that reads the oven thermometer every 100 ms
        Flux<Long> readings = Flux.interval(Duration.ZERO, Duration.ofMillis(100))
            .map(n -> 180 + n)
            .doOnSubscribe(s -> at("thermometer: reading started"))
            .doOnCancel(() -> at("thermometer: reading stopped"));

        Flux<Long> temperature = readings.replay(1).refCount(1, Duration.ofMillis(300));
        at("refCount returned; waiting 200 ms before the first screen");
        Thread.sleep(200);

        Disposable hall = temperature.subscribe();
        Disposable kitchen = temperature.subscribe();
        at("two screens subscribed");
        Thread.sleep(250);
        hall.dispose();
        kitchen.dispose();
        at("both screens left");
        Thread.sleep(500);
        at("done");
    }
}
