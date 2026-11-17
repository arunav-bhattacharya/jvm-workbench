// Java equivalent of CleanupAfterCancel.kt: a thread that was interrupted can't make a blocking
// cleanup call while its interrupt flag is set. Clear the flag for the cleanup, then restore it.
package workbench.coroutines.l05;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class CleanupAfterCancelJava {
    static void giveBack(String ticket) throws InterruptedException {
        Thread.sleep(50); // the phone call to the lending desk
        System.out.println("  gave back the pan on " + ticket);
    }

    public static void main(String[] args) throws Exception {
        boolean fixed = args.length > 0 && args[0].equals("fixed");
        ExecutorService pool = Executors.newSingleThreadExecutor();
        pool.submit(() -> {
            String ticket = "ticket-7";
            System.out.println("  borrowed the jam pan on " + ticket);
            try {
                Thread.sleep(10_000); // waiting for the jam to set
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt(); // keep the cancel request, as you should
            } finally {
                boolean wasInterrupted = fixed && Thread.interrupted(); // fixed: clear the flag for cleanup
                try {
                    giveBack(ticket);
                } catch (InterruptedException e) {
                    System.out.println("  giving back failed at once: InterruptedException");
                    Thread.currentThread().interrupt();
                }
                if (wasInterrupted) Thread.currentThread().interrupt(); // and put it back afterwards
            }
        });
        Thread.sleep(100);
        System.out.println(fixed ? "interrupt, flag cleared around giveBack:" : "interrupt, plain blocking call in finally:");
        pool.shutdownNow();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        System.out.println("  task finished");
    }
}
