package workbench.concurrency.l07;

import java.time.Duration;

/**
 * The bounded buffer from lesson 5 again, rebuilt with a {@link java.util.concurrent.locks.ReentrantLock}
 * and two {@link java.util.concurrent.locks.Condition}s: {@code notFull} for producers and
 * {@code notEmpty} for consumers.
 *
 * <ul>
 *   <li>{@link #put} waits on {@code notFull} while the buffer is full, then signals {@code notEmpty}.</li>
 *   <li>{@link #take} waits on {@code notEmpty} while it is empty, then signals {@code notFull}.</li>
 *   <li>{@link #offer} is {@code put} with a time limit: it returns false if no space opened up in time.</li>
 *   <li>Waiting threads give up with {@link InterruptedException} when interrupted.</li>
 * </ul>
 * Because each kind of waiter has its own condition, {@code signal()} (not {@code signalAll()}) is enough.
 */
public class LockBuffer<T> {
    private final int capacity;

    /** @throws IllegalArgumentException if {@code capacity} is less than 1 */
    public LockBuffer(int capacity) {
        this.capacity = capacity;
    }

    public void put(T item) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: lock; while full notFull.await(); add; notEmpty.signal(); unlock in finally");
    }

    /** Like put, but gives up and returns false if the buffer is still full after {@code timeout}. */
    public boolean offer(T item, Duration timeout) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: like put, but wait with notFull.awaitNanos(remaining)");
    }

    public T take() throws InterruptedException {
        throw new UnsupportedOperationException("TODO: lock; while empty notEmpty.await(); remove; notFull.signal(); unlock in finally");
    }

    public int size() {
        throw new UnsupportedOperationException("TODO: return the count, under the lock");
    }
}
