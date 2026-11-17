// Java equivalent of ContextElements.kt: a ThreadLocal does not follow a task to a pool thread.
// You copy it by hand (this is what logging libraries' executor wrappers do). JDK 25 adds ScopedValue
// (final in JDK 25, JEP 506), but the labs compile for Java 21, so this demo copies by hand.
package workbench.coroutines.l04;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ContextElementsJava {
    static final ThreadLocal<String> GUEST = new ThreadLocal<>();   // a note on the cook's apron

    // capture the caller's value now, install it around the task later, then restore
    static Runnable withGuest(Runnable task) {
        String captured = GUEST.get();
        return () -> {
            String previous = GUEST.get();
            GUEST.set(captured);
            try { task.run(); } finally { GUEST.set(previous); }
        };
    }

    public static void main(String[] args) {
        try (ExecutorService pool = Executors.newFixedThreadPool(2)) {
            GUEST.set("ana");
            System.out.println("main thread sees              " + GUEST.get());
            CompletableFuture.runAsync(() -> System.out.println("pool thread, plain ThreadLocal " + GUEST.get()), pool).join();
            CompletableFuture.runAsync(withGuest(() -> System.out.println("pool thread, copied by hand   " + GUEST.get())), pool).join();
        }
    }
}
