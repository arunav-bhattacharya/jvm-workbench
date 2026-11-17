package workbench.flows.l04;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

// Closest Java equivalent of Flow's buffer(n): a BlockingQueue between two threads.
// Java blocks a thread where Kotlin suspends a coroutine; the counting is the same.
public class AheadProbeJava {

    static void probe(String label, Supplier<BlockingQueue<Integer>> shelf) throws InterruptedException {
        BlockingQueue<Integer> queue = shelf.get();
        AtomicInteger returned = new AtomicInteger();          // put() calls that have returned
        CountDownLatch callEnds = new CountDownLatch(1);
        Thread cook = Thread.ofPlatform().daemon().start(() -> {
            try {
                for (int dumpling = 1; dumpling <= 200; dumpling++) { queue.put(dumpling); returned.set(dumpling); }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        Thread diner = Thread.ofPlatform().start(() -> {
            try {
                queue.take();                                   // dumpling 1 ...
                callEnds.await();                               // ... and then the phone rings
                for (int i = 2; i <= 200; i++) queue.take();
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        while (cook.getState() != Thread.State.WAITING) Thread.sleep(5);   // cook blocked in put()
        Thread.sleep(50);
        int ahead = returned.get();
        callEnds.countDown();
        diner.join();
        System.out.printf("%-26s puts returned while the diner held dumpling 1: %3d%n", label, ahead);
    }

    public static void main(String[] args) throws InterruptedException {
        probe("SynchronousQueue", SynchronousQueue::new);                    // like buffer(0)
        probe("ArrayBlockingQueue(1)", () -> new ArrayBlockingQueue<>(1));   // like buffer(1)
        probe("ArrayBlockingQueue(10)", () -> new ArrayBlockingQueue<>(10)); // like buffer(10)
        probe("ArrayBlockingQueue(64)", () -> new ArrayBlockingQueue<>(64)); // like buffer()
    }
}
