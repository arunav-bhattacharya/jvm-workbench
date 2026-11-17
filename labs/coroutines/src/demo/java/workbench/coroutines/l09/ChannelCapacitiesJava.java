// Java equivalent of ChannelCapacities.kt: blocking queues between two threads. SynchronousQueue
// is a rendezvous, ArrayBlockingQueue(2) has capacity 2, LinkedBlockingQueue is unbounded.
// The JDK has no conflated queue; Kotlin's CONFLATED channel keeps only the newest element.
// A blocking queue has no close(), so the cook sends a marker (-1) at the end instead.
package workbench.coroutines.l09;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.SynchronousQueue;

public class ChannelCapacitiesJava {
    static void run(String label, BlockingQueue<Integer> hatch) throws InterruptedException {
        long t0 = System.nanoTime();
        List<Long> sendTimes = new ArrayList<>();
        Thread cook = Thread.ofPlatform().start(() -> {
            try {
                for (int plate = 1; plate <= 5; plate++) { hatch.put(plate); sendTimes.add((System.nanoTime() - t0) / 1_000_000); }
                hatch.put(-1); // the end marker
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        List<Integer> received = new ArrayList<>();
        for (int plate = hatch.take(); plate != -1; plate = hatch.take()) { Thread.sleep(100); received.add(plate); }
        cook.join();
        System.out.printf("%-22s put() returned at %-26s received %s%n", label, sendTimes + " ms", received);
    }

    public static void main(String[] args) throws InterruptedException {
        run("SynchronousQueue", new SynchronousQueue<>());
        run("ArrayBlockingQueue(2)", new ArrayBlockingQueue<>(2));
        run("LinkedBlockingQueue", new LinkedBlockingQueue<>());
    }
}
