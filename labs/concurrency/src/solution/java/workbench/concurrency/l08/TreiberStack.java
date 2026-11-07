package workbench.concurrency.l08;

import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;

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

    public void push(T item) {
        Objects.requireNonNull(item, "item");
        while (true) {
            Node<T> top = head.get();                     // 1. read the current head
            Node<T> node = new Node<>(item, top);         // 2. build the new node off to the side
            if (head.compareAndSet(top, node)) return;    // 3. publish it only if the head is still `top`
        }                                                 // 4. otherwise another push or pop won: retry
    }

    public T pop() {
        while (true) {
            Node<T> top = head.get();
            if (top == null) return null;                 // empty
            if (head.compareAndSet(top, top.next)) {      // unlink the top node, if nobody else did
                return top.item;
            }
        }
    }

    public boolean isEmpty() {
        return head.get() == null;
    }
}
