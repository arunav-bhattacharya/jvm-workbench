// Java equivalent of ThreeWays.kt: the same request with virtual threads (plain blocking code)
// and with Reactor (operators, no blocking). Same total time: the slowest call.
package workbench.coroutines.l11;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import reactor.core.publisher.Mono;

public class ThreeWaysJava {
    static String call(String name, long ms) throws InterruptedException {
        Thread.sleep(ms); // a blocking client call
        return name;
    }

    static List<String> withVirtualThreads() throws Exception {
        try (ExecutorService vt = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<String> account = vt.submit(() -> call("account", 100));
            Future<String> ledger = vt.submit(() -> call("ledger", 300));
            Future<String> risk = vt.submit(() -> call("risk", 200));
            return List.of(account.get(), ledger.get(), risk.get());
        }
    }

    static List<String> withReactor() {
        return Mono.zip(
                Mono.just("account").delayElement(Duration.ofMillis(100)),
                Mono.just("ledger").delayElement(Duration.ofMillis(300)),
                Mono.just("risk").delayElement(Duration.ofMillis(200)))
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
