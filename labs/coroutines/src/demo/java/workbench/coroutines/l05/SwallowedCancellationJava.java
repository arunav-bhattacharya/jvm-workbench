// Java equivalent of SwallowedCancellation.kt: catching InterruptedException and carrying on
// swallows the cancel request, just as runCatching swallows CancellationException.
package workbench.coroutines.l05;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class SwallowedCancellationJava {
    static void pollSettlement(boolean restoreInterrupt, AtomicInteger attempts) {
        for (int i = 0; i < 20; i++) {
            try {
                attempts.incrementAndGet();  // the HTTP call to the acquirer would go here
                Thread.sleep(100);
            } catch (InterruptedException e) {
                if (restoreInterrupt) {
                    Thread.currentThread().interrupt();
                    return;                   // stop: somebody asked us to
                }
                // swallowed: the flag is now clear, so the next sleep() sleeps normally
            }
        }
    }

    public static void main(String[] args) throws Exception {
        boolean fixed = args.length > 0 && args[0].equals("fixed");
        AtomicInteger attempts = new AtomicInteger();
        ExecutorService pool = Executors.newSingleThreadExecutor();
        pool.submit(() -> pollSettlement(fixed, attempts));
        Thread.sleep(250);
        int cancelledAt = attempts.get();
        long asked = System.nanoTime();
        pool.shutdownNow();                   // interrupts the poller
        pool.awaitTermination(10, TimeUnit.SECONDS);
        long ms = (System.nanoTime() - asked) / 1_000_000;
        System.out.println(fixed ? "catch + restore the flag:" : "catch, swallowing:");
        System.out.printf("  attempts before cancel: %d, after cancel: %d, shutdown took %d ms%n",
            cancelledAt, attempts.get() - cancelledAt, ms);
    }
}
