package workbench.executors.l02;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Seven 500 ms tasks into new ThreadPoolExecutor(2, 4, ...). Where does each one go?
 * Args: queue (bounded | unbounded | handoff) and policy (abort | caller | discard | oldest).
 */
public class PoolPuzzleDemo {
    public static void main(String[] args) throws Exception {
        String queueKind = args.length > 0 ? args[0] : "bounded";
        String policyKind = args.length > 1 ? args[1] : "abort";
        BlockingQueue<Runnable> queue = switch (queueKind) {
            case "unbounded" -> new LinkedBlockingQueue<>();
            case "handoff" -> new SynchronousQueue<>();
            default -> new ArrayBlockingQueue<>(2);
        };
        RejectedExecutionHandler policy = switch (policyKind) {
            case "caller" -> new ThreadPoolExecutor.CallerRunsPolicy();
            case "discard" -> new ThreadPoolExecutor.DiscardPolicy();
            case "oldest" -> new ThreadPoolExecutor.DiscardOldestPolicy();
            default -> new ThreadPoolExecutor.AbortPolicy();
        };
        ThreadPoolExecutor pool = new ThreadPoolExecutor(2, 4, 60, TimeUnit.SECONDS, queue, policy);
        System.out.printf("core=2 max=4 queue=%s policy=%s%n", queueKind, policyKind);

        long t0 = System.nanoTime();
        for (int i = 1; i <= 7; i++) {
            int id = i;
            Runnable task = () -> {
                try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                System.out.printf("    task %d done on %s%n", id, Thread.currentThread().getName());
            };
            try {
                pool.execute(task);
                System.out.printf("task %d accepted: threads=%d queued=%d%n", id, pool.getPoolSize(), pool.getQueue().size());
            } catch (RejectedExecutionException e) {
                System.out.printf("task %d REJECTED: threads=%d queued=%d%n", id, pool.getPoolSize(), pool.getQueue().size());
            }
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        System.out.printf("all done in %d ms, completed tasks: %d%n",
                (System.nanoTime() - t0) / 1_000_000, pool.getCompletedTaskCount());
    }
}
