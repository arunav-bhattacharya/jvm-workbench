// Java equivalent of SwallowedCancellation.kt: catching InterruptedException and carrying on
// swallows the cancel request, just as runCatching swallows CancellationException.
package workbench.coroutines.l05;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class SwallowedCancellationJava {
    /** Phones the butcher 20 times, 100 ms apart. A failed call is logged and tried again. */
    static void phoneButcher(boolean restoreInterrupt, AtomicInteger calls) {
        for (int i = 0; i < 20; i++) {
            try {
                calls.incrementAndGet();     // the phone call to the butcher would go here
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
        AtomicInteger calls = new AtomicInteger();
        ExecutorService pool = Executors.newSingleThreadExecutor();
        pool.submit(() -> phoneButcher(fixed, calls));
        Thread.sleep(250);
        int cancelledAt = calls.get();
        long asked = System.nanoTime();
        pool.shutdownNow();                   // interrupts the caller
        pool.awaitTermination(10, TimeUnit.SECONDS);
        long ms = (System.nanoTime() - asked) / 1_000_000;
        System.out.println(fixed ? "catch + restore the flag:" : "catch, swallowing:");
        System.out.printf("  calls before cancel: %d, after cancel: %d, shutdown took %d ms%n",
            cancelledAt, calls.get() - cancelledAt, ms);
    }
}
