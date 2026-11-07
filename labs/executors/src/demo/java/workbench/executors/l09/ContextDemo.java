package workbench.executors.l09;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** A request id in a ThreadLocal, handed to a pool three ways. */
public class ContextDemo {
    static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();

    // capture on the submitting thread, install on the worker, always clean up
    static Runnable withContext(Runnable task) {
        String captured = REQUEST_ID.get();
        return () -> {
            String previous = REQUEST_ID.get();
            REQUEST_ID.set(captured);
            try {
                task.run();
            } finally {
                if (previous == null) REQUEST_ID.remove();
                else REQUEST_ID.set(previous);
            }
        };
    }

    public static void main(String[] args) throws Exception {
        try (ExecutorService pool = Executors.newFixedThreadPool(1)) {
            REQUEST_ID.set("req-42");
            pool.submit(() -> System.out.println("1. plain task sees:   " + REQUEST_ID.get())).get();
            pool.submit(withContext(() -> System.out.println("2. wrapped task sees: " + REQUEST_ID.get()))).get();

            // a task that sets the ThreadLocal itself and forgets to remove it
            pool.submit(() -> REQUEST_ID.set("req-7")).get();
            REQUEST_ID.remove();                                          // the next caller has no request
            pool.submit(() -> System.out.println("3. next task sees:    " + REQUEST_ID.get() + "  (left over from an earlier task)")).get();
        }
    }
}
