// Java equivalent of ChannelCapacities.kt: blocking queues between two threads. SynchronousQueue
// is a rendezvous, ArrayBlockingQueue(2) has capacity 2, LinkedBlockingQueue is unbounded.
// The JDK has no conflated queue; Kotlin's CONFLATED channel keeps only the newest element.
// A blocking queue has no close(), so the producer sends a marker (-1) at the end instead.
package workbench.coroutines.l09;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.SynchronousQueue;

public class ChannelCapacitiesJava {
    static void run(String label, BlockingQueue<Integer> queue) throws InterruptedException {
        long t0 = System.nanoTime();
        List<Long> sendTimes = new ArrayList<>();
        Thread producer = Thread.ofPlatform().start(() -> {
            try {
                for (int id = 1; id <= 5; id++) { queue.put(id); sendTimes.add((System.nanoTime() - t0) / 1_000_000); }
                queue.put(-1); // the end marker
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        List<Integer> received = new ArrayList<>();
        for (int id = queue.take(); id != -1; id = queue.take()) { Thread.sleep(100); received.add(id); }
        producer.join();
        System.out.printf("%-20s put() returned at %-26s received %s%n", label, sendTimes + " ms", received);
    }

    public static void main(String[] args) throws InterruptedException {
        run("SynchronousQueue", new SynchronousQueue<>());
        run("ArrayBlockingQueue(2)", new ArrayBlockingQueue<>(2));
        run("LinkedBlockingQueue", new LinkedBlockingQueue<>());
    }
}
