// Java equivalent of LeakedWork.kt: a request thread hands the refund to a shared pool.
// Interrupting the request (the client gave up) does not reach the pool's task.
// Pass "fixed" to run the refund in the request's own thread, so the interrupt stops it.
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

    static void refundSteps(String id) throws InterruptedException {
        for (int step = 0; step < 6; step++) {
            Thread.sleep(100);
            System.out.printf("  [%d ms] refund %s: step %d%n", ms(), id, step);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        boolean structured = args.length > 0 && args[0].equals("fixed");
        start = System.nanoTime();
        Thread request = Thread.ofVirtual().start(() -> {
            try {
                if (structured) refundSteps("r-17");                 // part of the request
                else SHARED.submit(() -> { refundSteps("r-17"); return null; }); // an orphan
                Thread.sleep(10_000);                                // the request goes on to other things
            } catch (InterruptedException e) {
                // the request was cancelled
            }
        });
        Thread.sleep(250);
        request.interrupt();
        System.out.printf("[%d ms] request interrupted (client gave up)%n", ms());
        Thread.sleep(500);
        System.out.printf("[%d ms] main done%n", ms());
    }
}
