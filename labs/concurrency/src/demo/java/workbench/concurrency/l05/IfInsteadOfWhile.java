package workbench.concurrency.l05;

import java.util.ArrayDeque;
import java.util.Deque;

/** Two consumers wait on an empty queue. One item arrives. The guard is an `if`. */
public class IfInsteadOfWhile {
    static final Object lock = new Object();
    static final Deque<String> queue = new ArrayDeque<>();

    static String take() throws InterruptedException {
        synchronized (lock) {
            if (queue.isEmpty()) {              // BUG: checked once, never again after waking
                lock.wait();
            }
            return queue.removeFirst();         // throws NoSuchElementException if someone else took it
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable consumer = () -> {
            try {
                System.out.println(Thread.currentThread().getName() + " took " + take());
            } catch (Exception e) {
                System.out.println(Thread.currentThread().getName() + " failed: " + e);
            }
        };
        Thread c1 = new Thread(consumer, "consumer-1");
        Thread c2 = new Thread(consumer, "consumer-2");
        c1.start();
        c2.start();
        while (c1.getState() != Thread.State.WAITING || c2.getState() != Thread.State.WAITING) {
            Thread.sleep(10);                   // wait until both are parked in wait()
        }
        synchronized (lock) {
            queue.addLast("auth-1");            // one item...
            lock.notifyAll();                   // ...and both consumers wake up
        }
        c1.join(2_000);
        c2.join(2_000);
        if (c1.isAlive() || c2.isAlive()) {     // with `while`, one consumer goes back to waiting
            System.out.println("one consumer is still waiting; giving it a second item");
            synchronized (lock) {
                queue.addLast("auth-2");
                lock.notifyAll();
            }
        }
        c1.join();
        c2.join();
    }
}
