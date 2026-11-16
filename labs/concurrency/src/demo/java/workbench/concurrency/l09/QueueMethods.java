package workbench.concurrency.l09;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.TimeUnit;

/** The kitchen's rail as a BlockingQueue: four ways to add to a full one, and two queues that surprise people. */
public class QueueMethods {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> q = new ArrayBlockingQueue<>(2);
        q.put("ticket-1");
        q.put("ticket-2");                                             // now full

        try { q.add("ticket-3"); } catch (IllegalStateException e) { System.out.println("add:            throws " + e); }
        System.out.println("offer:          " + q.offer("ticket-3"));
        long t0 = System.nanoTime();
        boolean timed = q.offer("ticket-3", 300, TimeUnit.MILLISECONDS);
        System.out.printf("offer(300 ms):  %s after %d ms%n", timed, (System.nanoTime() - t0) / 1_000_000);

        Thread waiter = new Thread(() -> {
            try { q.put("ticket-3"); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        waiter.start();
        Thread.sleep(200);
        System.out.println("put:            the waiter is " + waiter.getState() + " until a slot opens");
        System.out.println("take:           " + q.take() + " (frees a slot)");
        waiter.join();
        System.out.println("queue now:      " + q);

        try { q.offer(null); } catch (NullPointerException e) { System.out.println("offer(null):    throws NullPointerException"); }

        System.out.println("new LinkedBlockingQueue<>() capacity: " + new LinkedBlockingQueue<String>().remainingCapacity());
        System.out.println("SynchronousQueue.offer with no taker waiting: " + new SynchronousQueue<String>().offer("ticket-9"));
    }
}
