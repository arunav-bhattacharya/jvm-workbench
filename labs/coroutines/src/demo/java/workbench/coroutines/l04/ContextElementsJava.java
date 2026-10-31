// Java equivalent of ContextElements.kt: a ThreadLocal does not follow a task to a pool thread.
// You copy it by hand (this is what MDC-propagating executor wrappers do). JDK 25 adds ScopedValue
// (final in JDK 25, JEP 506), but the labs compile for Java 21, so this demo copies by hand.
package workbench.coroutines.l04;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ContextElementsJava {
    static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();

    // capture the caller's value now, install it around the task later, then restore
    static Runnable withRequestId(Runnable task) {
        String captured = REQUEST_ID.get();
        return () -> {
            String previous = REQUEST_ID.get();
            REQUEST_ID.set(captured);
            try { task.run(); } finally { REQUEST_ID.set(previous); }
        };
    }

    public static void main(String[] args) {
        try (ExecutorService pool = Executors.newFixedThreadPool(2)) {
            REQUEST_ID.set("req-42");
            System.out.println("main thread sees              " + REQUEST_ID.get());
            CompletableFuture.runAsync(() -> System.out.println("pool thread, plain ThreadLocal " + REQUEST_ID.get()), pool).join();
            CompletableFuture.runAsync(withRequestId(() -> System.out.println("pool thread, copied by hand   " + REQUEST_ID.get())), pool).join();
        }
    }
}
