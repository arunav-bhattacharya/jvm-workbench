// Java equivalent of SupervisorTrap.kt: a task sent to some other executor is not part of the
// request. Shutting the request's executor down interrupts its own tasks, not that one.
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
        ExecutorService request = Executors.newVirtualThreadPerTaskExecutor();
        shared.submit(() -> {
            try { Thread.sleep(300); stamp("detached task: still running, nobody cancelled me"); }
            catch (InterruptedException e) { stamp("detached task: interrupted"); }
        });
        request.submit(() -> {
            try { Thread.sleep(300); stamp("request task: done"); }
            catch (InterruptedException e) { stamp("request task: interrupted"); }
        });
        Thread.sleep(100);
        request.shutdownNow();
        request.awaitTermination(1, TimeUnit.SECONDS);
        stamp("request cancelled and joined");
        Thread.sleep(400);
        shared.shutdown();
        stamp("main done");
    }
}
