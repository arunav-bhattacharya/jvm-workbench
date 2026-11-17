// Java equivalent of SupervisorTrap.kt: a task sent to some other executor is not part of the
// dinner. Shutting the dinner's executor down interrupts its own tasks, not that one.
package workbench.coroutines.l06;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class SupervisorTrapJava {
    static long since;
    static void stamp(String msg) { System.out.printf("%5d ms  %s%n", (System.nanoTime() - since) / 1_000_000, msg); }

    public static void main(String[] args) throws Exception {
        since = System.nanoTime();
        ExecutorService shared = Executors.newCachedThreadPool();          // what launch(SupervisorJob()) amounts to
        ExecutorService dinner = Executors.newVirtualThreadPerTaskExecutor();
        shared.submit(() -> {
            try { Thread.sleep(300); stamp("detached task: still running, nobody cancelled me"); }
            catch (InterruptedException e) { stamp("detached task: interrupted"); }
        });
        dinner.submit(() -> {
            try { Thread.sleep(300); stamp("dinner task: done"); }
            catch (InterruptedException e) { stamp("dinner task: interrupted"); }
        });
        Thread.sleep(100);
        dinner.shutdownNow();
        dinner.awaitTermination(1, TimeUnit.SECONDS);
        stamp("dinner cancelled and joined");
        Thread.sleep(400);
        shared.shutdown();
        stamp("main done");
    }
}
