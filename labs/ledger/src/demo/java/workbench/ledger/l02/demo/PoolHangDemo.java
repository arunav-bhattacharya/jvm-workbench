package workbench.ledger.l02.demo;

import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Month-end statements on the ledger pool: each statement task asks the same 2-thread pool for a
 * balance and waits for the answer. Run it, then take a thread dump while it hangs.
 * Arg: how many seconds to stay hung (default 4).
 */
public class PoolHangDemo {
    public static void main(String[] args) throws InterruptedException {
        int seconds = args.length > 0 ? Integer.parseInt(args[0]) : 4;
        ThreadPoolExecutor pool = new ThreadPoolExecutor(2, 2, 0, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(100), Thread.ofPlatform().name("ledger-", 0).factory());
        for (String merchant : List.of("m-001", "m-002", "m-003")) {
            pool.submit(() -> statement(pool, merchant));
        }
        long pid = ProcessHandle.current().pid();
        System.out.printf("pid %d, hanging for %d s. In another terminal: jcmd %d Thread.print -l%n", pid, seconds, pid);
        Thread.sleep(seconds * 1_000L);
        System.out.printf("after %d s: active=%d, queued=%d, completed=%d%n",
                seconds, pool.getActiveCount(), pool.getQueue().size(), pool.getCompletedTaskCount());
        pool.shutdownNow();                                   // interrupts the two get() calls that will never return
    }

    static String statement(ExecutorService pool, String merchant) throws Exception {
        Future<Long> balance = pool.submit(() -> balanceOf(merchant));   // queued behind the other statements
        return merchant + ": " + balance.get();                          // waits for a thread that is never free
    }

    static long balanceOf(String merchant) {
        return 4_200;                                         // fast: the problem is not speed
    }
}
