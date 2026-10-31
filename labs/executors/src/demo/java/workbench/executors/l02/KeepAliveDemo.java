package workbench.executors.l02;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * A pool grows to max under a burst, then shrinks back when threads sit idle longer than keepAlive.
 * Pass "core" to call allowCoreThreadTimeOut(true) as well.
 */
public class KeepAliveDemo {
    public static void main(String[] args) throws Exception {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(2, 4, 300, TimeUnit.MILLISECONDS, new ArrayBlockingQueue<>(2));
        if (args.length > 0 && args[0].equals("core")) pool.allowCoreThreadTimeOut(true);

        System.out.println("before any task: threads=" + pool.getPoolSize());
        for (int i = 0; i < 6; i++) {
            pool.execute(() -> {
                try { Thread.sleep(200); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }
        long t0 = System.nanoTime();
        for (int tick = 0; tick <= 8; tick++) {
            System.out.printf("%4d ms: threads=%d active=%d queued=%d%n", (System.nanoTime() - t0) / 1_000_000,
                    pool.getPoolSize(), pool.getActiveCount(), pool.getQueue().size());
            Thread.sleep(150);
        }
        System.out.println("largest pool size seen: " + pool.getLargestPoolSize());
        pool.shutdown();
    }
}
