package workbench.generics.l06;

import java.util.Collection;
import java.util.Queue;

/** Java's version of the same idea: wildcards at the use site. */
public final class Transfers {
    private Transfers() {}

    /**
     * Moves every item from {@code from} into {@code to}, in queue order, and returns how many moved.
     * {@code from} is empty afterwards.
     *
     * TODO: {@code from} only gives you items, {@code to} only takes them. Change the parameter
     * types to the right wildcards (Producer Extends, Consumer Super), then write the body.
     * Afterwards a Queue<Integer> should drain into a Collection<Number>.
     */
    public static <T> int drainTo(Queue<T> from, Collection<T> to) {
        throw new UnsupportedOperationException("TODO: add ? extends / ? super, then poll until empty");
    }
}
