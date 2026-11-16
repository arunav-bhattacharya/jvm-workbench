package workbench.concurrency.l05;

import java.util.ArrayDeque;
import java.util.Deque;

/** Two cooks wait on an empty rail. One order arrives. The guard is an `if`. */
public class IfInsteadOfWhile {
    static final Object lock = new Object();
    static final Deque<String> rail = new ArrayDeque<>();

    static String take() throws InterruptedException {
        synchronized (lock) {
            if (rail.isEmpty()) {               // BUG: checked once, never again after waking
                lock.wait();
            }
            return rail.removeFirst();          // throws NoSuchElementException if someone else took it
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable cook = () -> {
            try {
                System.out.println(Thread.currentThread().getName() + " took " + take());
            } catch (Exception e) {
                System.out.println(Thread.currentThread().getName() + " failed: " + e);
            }
        };
        Thread c1 = new Thread(cook, "cook-1");
        Thread c2 = new Thread(cook, "cook-2");
        c1.start();
        c2.start();
        while (c1.getState() != Thread.State.WAITING || c2.getState() != Thread.State.WAITING) {
            Thread.sleep(10);                   // wait until both are parked in wait()
        }
        synchronized (lock) {
            rail.addLast("order-1");            // one order...
            lock.notifyAll();                   // ...and both cooks wake up
        }
        c1.join(2_000);
        c2.join(2_000);
        if (c1.isAlive() || c2.isAlive()) {     // with `while`, one cook goes back to waiting
            System.out.println("one cook is still waiting; giving it a second order");
            synchronized (lock) {
                rail.addLast("order-2");
                lock.notifyAll();
            }
        }
        c1.join();
        c2.join();
    }
}
