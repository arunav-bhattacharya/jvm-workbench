package workbench.memory.l03;

import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

public final class WeakListenerRegistry<L> {
    private final List<WeakReference<L>> listeners = new ArrayList<>();

    public synchronized void register(L listener) {
        listeners.add(new WeakReference<>(listener));   // the registry alone can't keep it alive
    }

    public void fire(Consumer<? super L> event) {
        List<L> alive = new ArrayList<>();
        synchronized (this) {
            listeners.removeIf(ref -> ref.get() == null);       // the GC cleared it: the listener is gone
            for (WeakReference<L> ref : listeners) {
                L l = ref.get();                                // a strong reference for the rest of fire()
                if (l != null) alive.add(l);
            }
        }
        for (L l : alive) event.accept(l);                      // call out without holding the lock
    }

    public synchronized int size() {
        listeners.removeIf(ref -> ref.get() == null);
        return listeners.size();
    }
}
