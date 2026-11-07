package workbench.memory.l03;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/**
 * Fraud-rule listeners register here to hear about each authorization. Rules are loaded and unloaded
 * at runtime, and a rule that was unloaded must not stay in memory just because it once registered.
 *
 * <p>Make the registry hold its listeners weakly: a listener stays registered only while something
 * else still refers to it. {@link #size()} and {@link #fire} must skip listeners the GC has cleared.
 */
public final class WeakListenerRegistry<L> {
    private final List<L> listeners = new CopyOnWriteArrayList<>();   // strong: keeps every listener alive forever

    public void register(L listener) {
        listeners.add(listener);
    }

    /** Calls {@code event} once for every listener that is still alive. */
    public void fire(Consumer<? super L> event) {
        for (L l : listeners) event.accept(l);
    }

    /** How many listeners are still alive. Drops the ones that were cleared. */
    public int size() {
        return listeners.size();
    }
}
