// Java equivalent of HandlerOnlyAtRoot.kt: execute() sends a task's exception to the thread's
// uncaught exception handler (like a root launch and its handler), while submit() keeps it
// inside the Future until someone calls get() (like a root async and await).
package workbench.coroutines.l06;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public class HandlerOnlyAtRootJava {
    public static void main(String[] args) throws Exception {
        Thread.UncaughtExceptionHandler handler = (t, e) -> System.out.println("  handler got: " + e.getCause().getMessage() + " (on " + t.getName() + ")");
        ExecutorService webhooks = Executors.newFixedThreadPool(2, r -> {
            Thread t = new Thread(r, "webhooks");
            t.setUncaughtExceptionHandler(handler);
            return t;
        });
        Runnable failing = () -> { throw new UncheckedIOException(new IOException("webhook 503")); };

        System.out.println("1. execute(): the exception reaches the thread's handler");
        webhooks.execute(failing);
        Thread.sleep(100);

        System.out.println("2. submit() that nobody waits for:");
        Future<?> f = webhooks.submit(failing);
        Thread.sleep(100);
        System.out.println("  nothing printed: the failure waits in the Future");
        try { f.get(); } catch (ExecutionException e) { System.out.println("  get threw: " + e.getCause().getCause().getMessage()); }

        webhooks.shutdown();
        webhooks.awaitTermination(5, TimeUnit.SECONDS);
    }
}
