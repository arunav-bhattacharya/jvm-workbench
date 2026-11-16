package workbench.concurrency.l11;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

/**
 * A waiter writes tickets of 100 numbered dishes and hands each one to a cook through the rail,
 * a queue. Run with -Pargs=reuse to rub out and reuse one ticket instead of handing over a new one.
 */
public class HandOff {
    public static void main(String[] args) throws InterruptedException {
        boolean reuse = args.length > 0 && args[0].equals("reuse");
        BlockingQueue<List<Integer>> queue = new ArrayBlockingQueue<>(4);
        int tickets = 5_000;
        int[] damaged = {0};

        Thread cook = new Thread(() -> {
            try {
                for (int b = 0; b < tickets; b++) {
                    List<Integer> ticket = queue.take();              // the cook owns this list now
                    try {
                        Object[] entries = ticket.toArray();
                        boolean ok = entries.length == 100;
                        for (int i = 0; ok && i < 100; i++) ok = entries[i].equals(((Integer) entries[0]) + i);
                        if (!ok) damaged[0]++;
                    } catch (RuntimeException e) {
                        damaged[0]++;                                 // a list changing under you can throw, too
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "cook");
        cook.start();

        List<Integer> shared = new ArrayList<>();
        for (int b = 0; b < tickets; b++) {
            List<Integer> ticket = reuse ? shared : new ArrayList<>(100);
            ticket.clear();                                           // with reuse: rubs out a ticket the cook may be reading
            for (int i = 0; i < 100; i++) ticket.add(b * 100 + i);
            queue.put(ticket);                                        // hand it over, and never touch it again
        }
        cook.join();
        System.out.printf("%s: %,d tickets handed over, %,d damaged%n", reuse ? "one ticket, reused" : "new ticket each time", tickets, damaged[0]);
    }
}
