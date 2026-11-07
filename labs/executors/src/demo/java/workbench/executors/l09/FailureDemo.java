package workbench.executors.l09;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadFactory;

/** Named threads with an UncaughtExceptionHandler. Which failures does the handler see? */
public class FailureDemo {
    public static void main(String[] args) throws Exception {
        ThreadFactory factory = Thread.ofPlatform()
                .name("ledger-", 0)                                       // ledger-0, ledger-1, ...
                .uncaughtExceptionHandler((t, e) -> System.out.println("  handler: " + t.getName() + " died of " + e))
                .factory();
        try (ExecutorService pool = Executors.newFixedThreadPool(1, factory)) {
            System.out.println("1. execute() a task that throws");
            pool.execute(() -> { throw new IllegalStateException("ledger row locked"); });
            Thread.sleep(200);
            System.out.println("   the next task runs on " + pool.submit(() -> Thread.currentThread().getName()).get());

            System.out.println("2. submit() a task that throws");
            Future<?> f = pool.submit(() -> { throw new IllegalStateException("negative amount"); });
            Thread.sleep(200);
            System.out.println("   (nothing printed) the next task runs on " + pool.submit(() -> Thread.currentThread().getName()).get());
            try {
                f.get();
            } catch (ExecutionException e) {
                System.out.println("   only get() shows it: " + e.getCause());
            }
        }
    }
}
