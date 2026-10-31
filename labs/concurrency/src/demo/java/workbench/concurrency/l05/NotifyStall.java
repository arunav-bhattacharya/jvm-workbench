package workbench.concurrency.l05;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.atomic.AtomicLong;

/** A one-slot buffer shared by 2 producers and 2 consumers. Uses notify(), or notifyAll() with -Pargs=all. */
public class NotifyStall {
    static final Object lock = new Object();
    static final Deque<Integer> slot = new ArrayDeque<>();
    static final AtomicLong moved = new AtomicLong();
    static boolean all;                         // set once in main, before the threads start

    static void put(int x) throws InterruptedException {
        synchronized (lock) {
            while (!slot.isEmpty()) lock.wait();
            slot.addLast(x);
            signal();                           // notify() wakes ONE waiter: maybe a consumer, maybe the other producer
        }
    }

    static int take() throws InterruptedException {
        synchronized (lock) {
            while (slot.isEmpty()) lock.wait();
            int x = slot.removeFirst();
            signal();
            return x;
        }
    }

    static void signal() {
        if (all) lock.notifyAll();
        else lock.notify();
    }

    public static void main(String[] args) throws InterruptedException {
        all = args.length > 0 && args[0].equals("all");
        System.out.println(all ? "using notifyAll()" : "using notify()");
        Thread[] threads = new Thread[4];
        for (int i = 0; i < 4; i++) {
            boolean producer = i < 2;
            threads[i] = new Thread(() -> {
                try {
                    while (true) {
                        if (producer) put(1);
                        else { take(); moved.incrementAndGet(); }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, (producer ? "producer-" : "consumer-") + (i % 2));
            threads[i].setDaemon(true);
            threads[i].start();
        }
        long last = -1;
        for (int second = 1; second <= 5; second++) {
            Thread.sleep(1_000);
            long now = moved.get();
            if (now == last) {
                System.out.printf("stalled after %,d items. Thread states:%n", now);
                for (Thread t : threads) System.out.println("  " + t.getName() + ": " + t.getState());
                return;
            }
            System.out.printf("after %d s: %,d items moved%n", second, now);
            last = now;
        }
        System.out.println(all ? "no stall: notifyAll() wakes every waiter, so the right kind always gets a turn"
                               : "no stall this time; it depends on timing, so run it again");
    }
}
