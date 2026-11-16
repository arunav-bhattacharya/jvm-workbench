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

    static void probe(String label, Supplier<BlockingQueue<Integer>> belt) throws InterruptedException {
        BlockingQueue<Integer> queue = belt.get();
        AtomicInteger returned = new AtomicInteger();          // put() calls that have returned
        CountDownLatch unlock = new CountDownLatch(1);
        Thread reader = Thread.ofPlatform().daemon().start(() -> {
            try {
                for (int seq = 1; seq <= 200; seq++) { queue.put(seq); returned.set(seq); }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        Thread writer = Thread.ofPlatform().start(() -> {
            try {
                queue.take();                                   // posting 1 ...
                unlock.await();                                 // ... is stuck behind a row lock
                for (int i = 2; i <= 200; i++) queue.take();
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        while (reader.getState() != Thread.State.WAITING) Thread.sleep(5);   // reader blocked in put()
        Thread.sleep(50);
        int ahead = returned.get();
        unlock.countDown();
        writer.join();
        System.out.printf("%-26s puts returned while the writer held posting 1: %3d%n", label, ahead);
    }

    public static void main(String[] args) throws InterruptedException {
        probe("SynchronousQueue", SynchronousQueue::new);                    // like buffer(0)
        probe("ArrayBlockingQueue(1)", () -> new ArrayBlockingQueue<>(1));   // like buffer(1)
        probe("ArrayBlockingQueue(10)", () -> new ArrayBlockingQueue<>(10)); // like buffer(10)
        probe("ArrayBlockingQueue(64)", () -> new ArrayBlockingQueue<>(64)); // like buffer()
    }
}
