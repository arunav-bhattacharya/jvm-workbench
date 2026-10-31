// Java equivalent of SequentialVsConcurrent.kt: blocking calls on virtual threads,
// started together with CompletableFuture and joined afterwards.
package workbench.coroutines.l02;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SequentialVsConcurrentJava {
    static String quote(String provider, long latencyMs) {
        try { Thread.sleep(latencyMs); } catch (InterruptedException e) { throw new RuntimeException(e); } // a network call
        return provider + ":" + latencyMs + "ms";
    }

    static final List<Map.Entry<String, Long>> LATENCIES =
        List.of(Map.entry("northbank", 300L), Map.entry("fjord-fx", 120L), Map.entry("tidewater", 200L));

    static List<String> sequential() {
        return LATENCIES.stream().map(e -> quote(e.getKey(), e.getValue())).toList();
    }

    static List<String> concurrent(ExecutorService vthreads) {
        List<CompletableFuture<String>> pending = LATENCIES.stream()
            .map(e -> CompletableFuture.supplyAsync(() -> quote(e.getKey(), e.getValue()), vthreads)) // start all
            .toList();
        return pending.stream().map(CompletableFuture::join).toList();                                // then wait
    }

    public static void main(String[] args) {
        try (ExecutorService vthreads = Executors.newVirtualThreadPerTaskExecutor()) {
            long t0 = System.nanoTime();
            List<String> r1 = sequential();
            System.out.printf("sequential: %s in %d ms%n", r1, (System.nanoTime() - t0) / 1_000_000);
            long t1 = System.nanoTime();
            List<String> r2 = concurrent(vthreads);
            System.out.printf("concurrent: %s in %d ms%n", r2, (System.nanoTime() - t1) / 1_000_000);
        }
    }
}
