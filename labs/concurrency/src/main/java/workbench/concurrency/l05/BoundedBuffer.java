package workbench.concurrency.l05;

/**
 * A fixed-size FIFO buffer between producer and consumer threads, built only with
 * {@code synchronized}, {@code wait()} and {@code notifyAll()}.
 *
 * <ul>
 *   <li>{@link #put} waits while the buffer is full, then adds the item at the tail.</li>
 *   <li>{@link #take} waits while the buffer is empty, then removes the item at the head.</li>
 *   <li>Waiting threads must use {@code wait()} with no timeout (so they show as WAITING),
 *       inside a {@code while} loop that re-checks the condition.</li>
 *   <li>Both methods give up with {@link InterruptedException} if their thread is interrupted while waiting.</li>
 * </ul>
 * Do not use anything from {@code java.util.concurrent}: this lesson is about doing it by hand.
 */
public class BoundedBuffer<T> {
    private final int capacity;

    /** @throws IllegalArgumentException if {@code capacity} is less than 1 */
    public BoundedBuffer(int capacity) {
        this.capacity = capacity;
    }

    /** Adds {@code item} at the tail, waiting while the buffer is full. */
    public void put(T item) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: while full, wait(); then add and notifyAll()");
    }

    /** Removes and returns the head, waiting while the buffer is empty. */
    public T take() throws InterruptedException {
        throw new UnsupportedOperationException("TODO: while empty, wait(); then remove and notifyAll()");
    }

    /** How many items are in the buffer right now. */
    public int size() {
        throw new UnsupportedOperationException("TODO: return the count, under the lock");
    }
}
