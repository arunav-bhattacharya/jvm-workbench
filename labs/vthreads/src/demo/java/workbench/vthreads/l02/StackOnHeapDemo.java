package workbench.vthreads.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

/**
 * Parks 10,000 virtual threads at a chosen call depth and measures how much heap they use.
 * A parked virtual thread keeps its stack frames in heap objects, so deeper stacks cost more heap.
 *
 * <p>Args: call depth before parking (default: runs 1 and 200).
 */
public class StackOnHeapDemo {
    static final int THREADS = 10_000;

    public static void main(String[] args) throws InterruptedException {
        int[] depths = args.length > 0 ? new int[] {Integer.parseInt(args[0])} : new int[] {1, 200};
        for (int depth : depths) measure(depth);
    }

    static void measure(int depth) throws InterruptedException {
        long base = usedHeap();
        CountDownLatch parked = new CountDownLatch(THREADS);
        CountDownLatch release = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>(THREADS);
        for (int i = 0; i < THREADS; i++) {
            threads.add(Thread.ofVirtual().start(() -> descend(depth, parked, release)));
        }
        parked.await();                               // every thread is now parked at the bottom of its stack
        long used = usedHeap() - base;
        System.out.printf("depth %3d: %,d parked virtual threads use about %,d MB of heap (%,d bytes each)%n",
                depth, THREADS, used / (1024 * 1024), used / THREADS);
        release.countDown();
        for (Thread t : threads) t.join();
    }

    // each level adds one stack frame; at the bottom the thread blocks and unmounts
    static int descend(int depth, CountDownLatch parked, CountDownLatch release) {
        if (depth > 1) return descend(depth - 1, parked, release) + 1;
        parked.countDown();
        try {
            release.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return 0;
    }

    static long usedHeap() throws InterruptedException {
        Runtime rt = Runtime.getRuntime();
        for (int i = 0; i < 2; i++) {
            System.gc();
            Thread.sleep(50);
        }
        return rt.totalMemory() - rt.freeMemory();
    }
}
