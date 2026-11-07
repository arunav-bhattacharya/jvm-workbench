package workbench.concurrency.l11;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

/**
 * A request thread fills batches of 100 ledger entries and hands each one to a writer thread
 * through a queue. Run with -Pargs=reuse to reuse one list instead of handing over a new one.
 */
public class HandOff {
    public static void main(String[] args) throws InterruptedException {
        boolean reuse = args.length > 0 && args[0].equals("reuse");
        BlockingQueue<List<Integer>> queue = new ArrayBlockingQueue<>(4);
        int batches = 5_000;
        int[] damaged = {0};

        Thread writer = new Thread(() -> {
            try {
                for (int b = 0; b < batches; b++) {
                    List<Integer> batch = queue.take();               // the writer owns this list now
                    try {
                        Object[] entries = batch.toArray();
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
        }, "ledger-writer");
        writer.start();

        List<Integer> shared = new ArrayList<>();
        for (int b = 0; b < batches; b++) {
            List<Integer> batch = reuse ? shared : new ArrayList<>(100);
            batch.clear();                                            // with reuse: clears a list the writer may be reading
            for (int i = 0; i < 100; i++) batch.add(b * 100 + i);
            queue.put(batch);                                         // hand it over, and never touch it again
        }
        writer.join();
        System.out.printf("%s: %,d batches handed over, %,d damaged%n", reuse ? "reused list" : "new list each time", batches, damaged[0]);
    }
}
