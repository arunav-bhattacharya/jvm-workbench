// Java equivalent of CancelABusyLoop.kt: Future.cancel(true) only sets the interrupt flag.
// A CPU loop stops only if it looks at the flag.
package workbench.coroutines.l05;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public class CancelABusyLoopJava {
    static final long ROWS = 60_000_000L;
    static volatile long sink; // keeps the JIT from deleting loops whose result nobody reads

    /** Pure CPU work: a checksum over one fake card number. 60 million of them take about 1.5 s. */
    static long checksum(long i) {
        long x = i;
        for (int k = 0; k < 20; k++) {
            x ^= x >>> 33;
            x *= -0xae502812aa7333L;
            x ^= x >>> 29;
        }
        return x;
    }

    public static void main(String[] args) throws Exception {
        Map<String, Runnable> loops = new LinkedHashMap<>();
        loops.put("no check", () -> {
            long sum = 0;
            for (long i = 0; i < ROWS; i++) sum += checksum(i);
            sink = sum;
        });
        loops.put("isInterrupted() every 1,000", () -> {
            long sum = 0;
            for (long i = 0; i < ROWS; i++) {
                if (i % 1_000 == 0 && Thread.currentThread().isInterrupted()) break;
                sum += checksum(i);
            }
            sink = sum;
        });
        ExecutorService pool = Executors.newSingleThreadExecutor(); // one thread, so the no-op below waits for it
        for (var e : loops.entrySet()) {
            Future<?> f = pool.submit(e.getValue());
            Thread.sleep(100); // let it get going
            long asked = System.nanoTime();
            f.cancel(true);    // sets the interrupt flag; the future reports "cancelled" at once
            // wait for the thread itself to come back: the no-op runs only once the loop has stopped
            pool.submit(() -> { }).get();
            System.out.printf("%-28s stopped %5d ms after cancel(true)%n", e.getKey(), (System.nanoTime() - asked) / 1_000_000);
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
    }
}
