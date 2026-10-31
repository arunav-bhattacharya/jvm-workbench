package workbench.concurrency.l05;

import java.util.ArrayDeque;
import java.util.Deque;

public class BoundedBuffer<T> {
    private final Object lock = new Object();     // private: no outside code can wait or notify on it
    private final Deque<T> items = new ArrayDeque<>();
    private final int capacity;

    public BoundedBuffer(int capacity) {
        if (capacity < 1) throw new IllegalArgumentException("capacity must be at least 1, was " + capacity);
        this.capacity = capacity;
    }

    public void put(T item) throws InterruptedException {
        synchronized (lock) {
            // 1. guard: re-check after every wake-up (spurious, or another producer got here first)
            while (items.size() == capacity) {
                lock.wait();                      // releases the lock while waiting, retakes it before returning
            }
            // 2. act: the condition holds and we hold the lock
            items.addLast(item);
            // 3. signal: the buffer changed. notifyAll, because producers and consumers share one wait set
            lock.notifyAll();
        }
    }

    public T take() throws InterruptedException {
        synchronized (lock) {
            while (items.isEmpty()) {
                lock.wait();
            }
            T head = items.removeFirst();
            lock.notifyAll();
            return head;
        }
    }

    public int size() {
        synchronized (lock) {
            return items.size();
        }
    }
}
