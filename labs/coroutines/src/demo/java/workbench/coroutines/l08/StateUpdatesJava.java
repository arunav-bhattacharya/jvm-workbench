// Java equivalent of StateUpdates.kt: the same read-modify-write race on an AtomicReference,
// fixed the same way, with a compare-and-set loop (updateAndGet).
package workbench.coroutines.l08;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

public class StateUpdatesJava {
    static void addCents(String label, Consumer<AtomicReference<Long>> add) {
        AtomicReference<Long> capturedCents = new AtomicReference<>(0L);
        try (ExecutorService pool = Executors.newFixedThreadPool(8)) {
            for (int t = 0; t < 8; t++) pool.submit(() -> { for (int i = 0; i < 100_000; i++) add.accept(capturedCents); });
        }
        System.out.printf("%-34s expected 800000, got %d%n", label, capturedCents.get());
    }

    public static void main(String[] args) {
        addCents("set(get() + 1)", ref -> ref.set(ref.get() + 1));              // read-modify-write: loses updates
        addCents("updateAndGet(c -> c + 1)", ref -> ref.updateAndGet(c -> c + 1)); // compare-and-set in a loop
    }
}
