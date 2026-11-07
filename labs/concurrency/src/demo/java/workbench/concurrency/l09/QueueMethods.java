package workbench.concurrency.l09;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.TimeUnit;

/** The four ways to add to a full BlockingQueue, and two queues that surprise people. */
public class QueueMethods {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> q = new ArrayBlockingQueue<>(2);
        q.put("e-1");
        q.put("e-2");                                                  // now full

        try { q.add("e-3"); } catch (IllegalStateException e) { System.out.println("add:            throws " + e); }
        System.out.println("offer:          " + q.offer("e-3"));
        long t0 = System.nanoTime();
        boolean timed = q.offer("e-3", 300, TimeUnit.MILLISECONDS);
        System.out.printf("offer(300 ms):  %s after %d ms%n", timed, (System.nanoTime() - t0) / 1_000_000);

        Thread producer = new Thread(() -> {
            try { q.put("e-3"); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        producer.start();
        Thread.sleep(200);
        System.out.println("put:            producer is " + producer.getState() + " until space opens");
        System.out.println("take:           " + q.take() + " (frees a slot)");
        producer.join();
        System.out.println("queue now:      " + q);

        try { q.offer(null); } catch (NullPointerException e) { System.out.println("offer(null):    throws NullPointerException"); }

        System.out.println("new LinkedBlockingQueue<>() capacity: " + new LinkedBlockingQueue<String>().remainingCapacity());
        System.out.println("SynchronousQueue.offer with no taker waiting: " + new SynchronousQueue<String>().offer("e-9"));
    }
}
