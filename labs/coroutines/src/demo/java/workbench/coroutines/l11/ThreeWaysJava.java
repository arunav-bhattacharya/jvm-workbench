// Java equivalent of ThreeWays.kt: the same dinner with virtual threads (plain blocking code)
// and with Reactor (operators, no blocking). Same total time: the slowest dish.
package workbench.coroutines.l11;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import reactor.core.publisher.Mono;

public class ThreeWaysJava {
    static String cook(String dish, long ms) throws InterruptedException {
        Thread.sleep(ms); // a blocking call
        return dish;
    }

    static List<String> withVirtualThreads() throws Exception {
        try (ExecutorService vt = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<String> soup = vt.submit(() -> cook("soup", 100));
            Future<String> roast = vt.submit(() -> cook("roast", 300));
            Future<String> salad = vt.submit(() -> cook("salad", 200));
            return List.of(soup.get(), roast.get(), salad.get());
        }
    }

    static List<String> withReactor() {
        return Mono.zip(
                Mono.just("soup").delayElement(Duration.ofMillis(100)),
                Mono.just("roast").delayElement(Duration.ofMillis(300)),
                Mono.just("salad").delayElement(Duration.ofMillis(200)))
            .map(t -> List.of(t.getT1(), t.getT2(), t.getT3()))
            .block();
    }

    public static void main(String[] args) throws Exception {
        withVirtualThreads(); withReactor(); // warm up
        long t0 = System.nanoTime();
        System.out.println("virtual threads: " + withVirtualThreads());
        System.out.println("  took " + (System.nanoTime() - t0) / 1_000_000 + " ms");
        t0 = System.nanoTime();
        System.out.println("reactor:         " + withReactor());
        System.out.println("  took " + (System.nanoTime() - t0) / 1_000_000 + " ms");
    }
}
