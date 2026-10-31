package workbench.concurrency.l07;

import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class LockBuffer<T> {
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();    // producers wait here
    private final Condition notEmpty = lock.newCondition();   // consumers wait here
    private final Deque<T> items = new ArrayDeque<>();
    private final int capacity;

    public LockBuffer(int capacity) {
        if (capacity < 1) throw new IllegalArgumentException("capacity must be at least 1, was " + capacity);
        this.capacity = capacity;
    }

    public void put(T item) throws InterruptedException {
        lock.lockInterruptibly();               // an interrupt can stop us even while we wait for the lock
        try {
            while (items.size() == capacity) {  // 1. guard: same while loop as with wait()
                notFull.await();
            }
            items.addLast(item);                // 2. act
            notEmpty.signal();                  // 3. wake ONE consumer: only consumers wait on notEmpty
        } finally {
            lock.unlock();                      // always in finally
        }
    }

    public boolean offer(T item, Duration timeout) throws InterruptedException {
        long nanos = timeout.toNanos();
        lock.lockInterruptibly();
        try {
            while (items.size() == capacity) {
                if (nanos <= 0) return false;
                nanos = notFull.awaitNanos(nanos);   // returns the time still left
            }
            items.addLast(item);
            notEmpty.signal();
            return true;
        } finally {
            lock.unlock();
        }
    }

    public T take() throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (items.isEmpty()) {
                notEmpty.await();
            }
            T head = items.removeFirst();
            notFull.signal();                   // wake ONE producer
            return head;
        } finally {
            lock.unlock();
        }
    }

    public int size() {
        lock.lock();
        try {
            return items.size();
        } finally {
            lock.unlock();
        }
    }
}
