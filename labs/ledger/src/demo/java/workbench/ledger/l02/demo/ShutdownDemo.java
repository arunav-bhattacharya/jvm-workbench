package workbench.ledger.l02.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Callable;
import java.util.concurrent.FutureTask;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 1,000 transfers wait on 8 threads at 5 ms each, then the service stops. Where does each one end up?
 * Args: "naive" or "drain" (the default), then the grace period in ms (default 100).
 */
public class ShutdownDemo {
    record Transfer(int id) {}

    // a FutureTask that remembers its transfer, so the queue hands back transfers, not anonymous Runnables
    static final class TransferTask extends FutureTask<Boolean> {
        final Transfer transfer;

        TransferTask(Transfer transfer, Callable<Boolean> work) {
            super(work);
            this.transfer = transfer;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String mode = args.length > 0 ? args[0] : "drain";
        long graceMs = args.length > 1 ? Long.parseLong(args[1]) : 100;
        ThreadPoolExecutor pool = new ThreadPoolExecutor(8, 8, 0, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(1_000), Thread.ofPlatform().name("ledger-", 0).factory());
        AtomicInteger applied = new AtomicInteger(), interrupted = new AtomicInteger();
        List<TransferTask> accepted = new ArrayList<>();
        for (int i = 0; i < 1_000; i++) {
            TransferTask task = new TransferTask(new Transfer(i), () -> {
                try {
                    Thread.sleep(5);                          // the journal write
                } catch (InterruptedException e) {
                    interrupted.incrementAndGet();            // not journaled, so not applied
                    throw e;
                }
                applied.incrementAndGet();
                return true;
            });
            pool.execute(task);
            accepted.add(task);
        }
        int handedBack = 0;
        if (mode.equals("naive")) {
            pool.shutdownNow();                               // the list of queued tasks it returns is dropped
        } else {
            pool.shutdown();                                  // 1. no new work; the queue keeps draining
            if (!pool.awaitTermination(graceMs, TimeUnit.MILLISECONDS)) {
                List<Runnable> neverStarted = pool.shutdownNow();                   // 2. interrupt, take back the queue
                for (Runnable r : neverStarted) ((TransferTask) r).cancel(false);   // 3. wake anyone waiting on them
                handedBack = neverStarted.size();             // 4. log these ids, or replay them on restart
            }
        }
        pool.awaitTermination(5, TimeUnit.SECONDS);
        long neverComplete = accepted.stream().filter(t -> !t.isDone()).count();
        System.out.printf("%s, grace %d ms: accepted 1,000 | applied %,d | interrupted %d | handed back %,d | lost %,d%n",
                mode, graceMs, applied.get(), interrupted.get(), handedBack,
                1_000 - applied.get() - interrupted.get() - handedBack);
        System.out.printf("futures that will never complete: %,d%n", neverComplete);
    }
}
