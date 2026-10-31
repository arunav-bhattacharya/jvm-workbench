package workbench.generics.l06;

import java.util.Collection;
import java.util.Queue;

public final class Transfers {
    private Transfers() {}

    // from produces T (extends), to consumes T (super)
    public static <T> int drainTo(Queue<? extends T> from, Collection<? super T> to) {
        int moved = 0;
        for (T item = from.poll(); item != null; item = from.poll()) {
            to.add(item);
            moved++;
        }
        return moved;
    }
}
