// Java equivalent of CleanupAfterCancel.kt: a thread that was interrupted can't make a blocking
// cleanup call while its interrupt flag is set. Clear the flag for the cleanup, then restore it.
package workbench.coroutines.l05;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class CleanupAfterCancelJava {
    static void releaseHold(String id) throws InterruptedException {
        Thread.sleep(50); // the network call to the issuer
        System.out.println("  released " + id);
    }

    public static void main(String[] args) throws Exception {
        boolean fixed = args.length > 0 && args[0].equals("fixed");
        ExecutorService pool = Executors.newSingleThreadExecutor();
        pool.submit(() -> {
            String hold = "hold-4250";
            System.out.println("  placed " + hold);
            try {
                Thread.sleep(10_000); // waiting for the customer's 3-D Secure challenge
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt(); // keep the cancel request, as you should
            } finally {
                boolean wasInterrupted = fixed && Thread.interrupted(); // fixed: clear the flag for cleanup
                try {
                    releaseHold(hold);
                } catch (InterruptedException e) {
                    System.out.println("  release failed at once: InterruptedException");
                    Thread.currentThread().interrupt();
                }
                if (wasInterrupted) Thread.currentThread().interrupt(); // and put it back afterwards
            }
        });
        Thread.sleep(100);
        System.out.println(fixed ? "interrupt, flag cleared around the release:" : "interrupt, plain blocking call in finally:");
        pool.shutdownNow();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        System.out.println("  task finished");
    }
}
