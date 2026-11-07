package workbench.concurrency.l07;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

/**
 * 4 producers and 4 consumers move 20,000 items through a one-slot buffer, twice:
 * once with one Condition and signalAll(), once with notFull/notEmpty and signal().
 * A wake-up is "wasted" when the thread wakes, re-checks, and has to wait again.
 */
public class WakeupCount {

    static final class Buffer {
        final ReentrantLock lock = new ReentrantLock();
        final Condition notFull;
        final Condition notEmpty;
        final boolean shared;
        final ArrayDeque<Integer> items = new ArrayDeque<>();
        long wasted;                                      // guarded by lock

        Buffer(boolean oneCondition) {
            shared = oneCondition;
            notFull = lock.newCondition();
            notEmpty = oneCondition ? notFull : lock.newCondition();   // same queue, or two
        }

        void put(int x) throws InterruptedException {
            lock.lock();
            try {
                while (items.size() == 1) {
                    notFull.await();
                    if (items.size() == 1) wasted++;      // woke up for nothing
                }
                items.add(x);
                if (shared) notEmpty.signalAll(); else notEmpty.signal();
            } finally {
                lock.unlock();
            }
        }

        int take() throws InterruptedException {
            lock.lock();
            try {
                while (items.isEmpty()) {
                    notEmpty.await();
                    if (items.isEmpty()) wasted++;
                }
                int x = items.remove();
                if (shared) notFull.signalAll(); else notFull.signal();
                return x;
            } finally {
                lock.unlock();
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (boolean one : new boolean[] {true, false}) {
            Buffer buffer = new Buffer(one);
            List<Thread> threads = new ArrayList<>();
            for (int i = 0; i < 4; i++) {
                threads.add(new Thread(() -> {
                    try { for (int n = 0; n < 5_000; n++) buffer.put(n); } catch (InterruptedException e) { return; }
                }));
                threads.add(new Thread(() -> {
                    try { for (int n = 0; n < 5_000; n++) buffer.take(); } catch (InterruptedException e) { return; }
                }));
            }
            long t0 = System.nanoTime();
            for (Thread t : threads) t.start();
            for (Thread t : threads) t.join();
            System.out.printf("%-34s wasted wake-ups: %,9d   (%d ms)%n",
                    one ? "one condition, signalAll():" : "notFull + notEmpty, signal():",
                    buffer.wasted, (System.nanoTime() - t0) / 1_000_000);
        }
    }
}
