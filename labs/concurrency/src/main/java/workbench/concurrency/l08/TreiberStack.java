package workbench.concurrency.l08;

import java.util.concurrent.atomic.AtomicReference;

/**
 * A lock-free stack (R. Kent Treiber, 1986): a linked list whose head lives in an
 * {@link AtomicReference}. Nodes never change once built; every push and pop swaps the head
 * with {@code compareAndSet} and retries if another thread got there first.
 *
 * <p>No {@code synchronized}, no locks.
 */
public class TreiberStack<T> {
    private static final class Node<T> {
        final T item;
        final Node<T> next;

        Node(T item, Node<T> next) {
            this.item = item;
            this.next = next;
        }
    }

    private final AtomicReference<Node<T>> head = new AtomicReference<>();

    /**
     * Pushes {@code item} on top.
     *
     * @throws NullPointerException if {@code item} is null (pop uses null to mean "empty")
     */
    public void push(T item) {
        throw new UnsupportedOperationException("TODO: build a node pointing at the current head, CAS the head to it, retry on failure");
    }

    /** Removes and returns the top item, or returns null if the stack is empty. */
    public T pop() {
        throw new UnsupportedOperationException("TODO: read the head; null means empty; CAS the head to head.next, retry on failure");
    }

    /** True if the stack held no items at the moment of the call. */
    public boolean isEmpty() {
        throw new UnsupportedOperationException("TODO: look at the head");
    }
}
