package workbench.container.l02;

import java.util.function.Supplier;

/** Holds one lazily created instance. Safe when many threads ask for it at the same time. */
public final class SingletonCell<T> {
    private final Supplier<T> factory;
    private volatile T instance;          // volatile: a thread that sees it non-null also sees a fully built object

    public SingletonCell(Supplier<T> factory) {
        this.factory = factory;
    }

    public T get() {
        T value = instance;               // 1. the fast path: one volatile read, no lock
        if (value == null) {
            synchronized (this) {
                value = instance;         // 2. check again: another thread may have built it while we waited
                if (value == null) {
                    value = factory.get();
                    instance = value;     // 3. publish; if the factory threw, nothing is stored and the next call retries
                }
            }
        }
        return value;
    }
}
