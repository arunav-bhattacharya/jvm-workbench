package workbench.concurrency.l12;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

/**
 * Closing time in the kitchen: two waiters (producers), three cooks (consumers), one bounded rail,
 * shut down with poison pills. Run with -Pargs=onepill to send a single pill instead of one per cook.
 */
public class PoisonPills {
    @SuppressWarnings("StringOperationCanBeSimplified")
    static final String PILL = new String("PILL");             // compared by identity

    public static void main(String[] args) throws InterruptedException {
        boolean onePill = args.length > 0 && args[0].equals("onepill");
        BlockingQueue<String> queue = new ArrayBlockingQueue<>(4);
        List<Thread> cooks = new ArrayList<>();
        for (int c = 0; c < 3; c++) {
            Thread t = new Thread(() -> {
                int done = 0;
                try {
                    while (true) {
                        String r = queue.take();
                        if (r == PILL) break;                  // this cook stops; the others keep going
                        done++;
                    }
                    System.out.println(Thread.currentThread().getName() + " got its pill after " + done + " orders");
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "cook-" + c);
            t.setDaemon(true);
            t.start();
            cooks.add(t);
        }
        Thread[] waiters = new Thread[2];
        for (int p = 0; p < 2; p++) {
            int me = p;
            waiters[p] = new Thread(() -> {
                try {
                    for (int i = 0; i < 1_000; i++) queue.put("order-" + me + "-" + i);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "waiter-" + p);
            waiters[p].start();
        }
        for (Thread t : waiters) t.join();                      // 1. every waiter is done...
        for (int c = 0; c < (onePill ? 1 : cooks.size()); c++) queue.put(PILL);   // 2. ...then one pill each
        for (Thread t : cooks) t.join(1_000);
        List<Thread> stuck = cooks.stream().filter(Thread::isAlive).toList();
        System.out.println("cooks still waiting: " + stuck.size()
                + (stuck.isEmpty() ? "" : " (" + stuck.get(0).getState() + " in take)"));
    }
}
