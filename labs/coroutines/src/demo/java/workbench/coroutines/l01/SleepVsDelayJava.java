// Java equivalent of SleepVsDelay.kt: one thread, five pots that simmer 200 ms each.
// A non-blocking timer callback plays the role of delay; Thread.sleep blocks the one thread.
package workbench.coroutines.l01;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class SleepVsDelayJava {
    public static void main(String[] args) {
        boolean blocking = args.length > 0 && args[0].equals("sleep");
        ExecutorService oneThread = Executors.newSingleThreadExecutor(r -> new Thread(r, "the-cook"));
        long t0 = System.nanoTime();
        List<CompletableFuture<Void>> pots = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            int id = i;
            CompletableFuture<Void> done = new CompletableFuture<>();
            oneThread.execute(() -> {
                System.out.println("pot " + id + " starts simmering on " + Thread.currentThread().getName());
                if (blocking) {
                    sleep(200);                 // holds the only thread
                    done.complete(null);
                } else {                        // a timer completes it later; the thread is free meanwhile
                    CompletableFuture.delayedExecutor(200, TimeUnit.MILLISECONDS, oneThread).execute(() -> done.complete(null));
                }
            });
            pots.add(done);
        }
        CompletableFuture.allOf(pots.toArray(CompletableFuture[]::new)).join();
        oneThread.shutdown();
        String how = blocking ? "Thread.sleep" : "a timer callback";
        System.out.printf("5 pots of 200 ms with %s took %d ms%n", how, (System.nanoTime() - t0) / 1_000_000);
    }

    private static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
