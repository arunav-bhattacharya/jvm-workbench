package workbench.concurrency.l03;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

public final class Hammer {
    private Hammer() {}

    public static void run(int threads, Runnable task) throws InterruptedException {
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> started = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            Thread t = new Thread(() -> {
                ready.countDown();          // "I'm at the start line"
                try {
                    go.await();             // wait for the starting gun
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                task.run();
            }, "hammer-" + i);
            t.start();
            started.add(t);
        }
        ready.await();                      // every thread is parked on the latch
        go.countDown();                     // release them all at once
        for (Thread t : started) t.join();  // wait for every one to finish
    }
}
