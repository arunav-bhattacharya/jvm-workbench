package workbench.performance.l05;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/** Four threads writing reports for a few seconds: CPU work, allocation, a slow document store and a shared lock. */
public final class ReportWorkload {
    private static final Object ARCHIVE = new Object();

    private ReportWorkload() { }

    static long countWords(String line) {                  // allocates: a new String for every word
        return line.split(" ").length;
    }

    static long callStore(String shelf, int doc) throws InterruptedException {
        StoreCallEvent event = new StoreCallEvent();
        event.begin();
        Thread.sleep(ThreadLocalRandom.current().nextInt(2, shelf.equals("shelf-7") ? 40 : 12));   // shelf 7 is slow
        boolean found = doc % 17 != 0;                     // now and then a document is missing
        long words = found ? 200 + doc % 3_000 : 0;
        event.end();
        if (event.shouldCommit()) {                         // skip the field work when no recording wants it
            event.shelf = shelf;
            event.words = words;
            event.found = found;
            event.commit();
        }
        return words;
    }

    static void reportLoop(int worker, long untilNanos) {
        long sink = 0;
        int i = 0;
        try {
            while (System.nanoTime() < untilNanos) {
                for (int k = 0; k < 2_000; k++) sink += countWords("page " + (k + i) % 9_000 + " of the weekly report on rain");
                sink += callStore("shelf-" + (i % 10), i);
                if (i % 10 == worker) {
                    synchronized (ARCHIVE) { Thread.sleep(15); }   // writing to the shared archive holds its lock
                }
                i++;
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        if (sink == 42) System.out.println();
    }

    static void run(int seconds) throws InterruptedException {
        long until = System.nanoTime() + seconds * 1_000_000_000L;
        List<Thread> threads = new ArrayList<>();
        for (int w = 0; w < 4; w++) {
            int worker = w;
            Thread t = new Thread(() -> reportLoop(worker, until), "report-" + w);
            t.start();
            threads.add(t);
        }
        for (Thread t : threads) t.join();
    }
}
