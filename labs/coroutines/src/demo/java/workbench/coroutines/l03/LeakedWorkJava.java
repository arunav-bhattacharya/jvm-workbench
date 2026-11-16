// Java equivalent of LeakedWork.kt: the dinner thread hands the stock pot to a shared pool.
// Interrupting the dinner (the guests called it off) does not reach the pool's task.
// Pass "fixed" to simmer the stock in the dinner's own thread, so the interrupt stops it.
package workbench.coroutines.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class LeakedWorkJava {
    static final ExecutorService SHARED = Executors.newCachedThreadPool(r -> {   // lives as long as the app
        Thread t = new Thread(r, "shared-pool");
        t.setDaemon(true);
        return t;
    });
    static long start;
    static long ms() { return (System.nanoTime() - start) / 1_000_000; }

    static void simmerStock(String pot) throws InterruptedException {
        for (int step = 0; step < 6; step++) {
            Thread.sleep(100);
            System.out.printf("  [%d ms] %s: still simmering, step %d%n", ms(), pot, step);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        boolean structured = args.length > 0 && args[0].equals("fixed");
        start = System.nanoTime();
        Thread dinner = Thread.ofVirtual().start(() -> {
            try {
                if (structured) simmerStock("stock pot");                            // part of the dinner
                else SHARED.submit(() -> { simmerStock("stock pot"); return null; }); // an orphan
                Thread.sleep(10_000);                                                // the dinner goes on
            } catch (InterruptedException e) {
                // the dinner was cancelled
            }
        });
        Thread.sleep(250);
        dinner.interrupt();
        System.out.printf("[%d ms] dinner interrupted (the guests called it off)%n", ms());
        Thread.sleep(500);
        System.out.printf("[%d ms] main done%n", ms());
    }
}
