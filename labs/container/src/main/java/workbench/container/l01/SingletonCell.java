package workbench.container.l01;

import java.util.function.Supplier;

/**
 * Holds one lazily created instance. Safe when many threads ask for it at the same time.
 *
 * <p>Write {@link #get()} with double-checked locking: read the volatile field once; if it is
 * null, lock, read it again, and only then call the factory and store the result. The factory
 * must run once, even when eight threads arrive together.
 */
public final class SingletonCell<T> {
    private final Supplier<T> factory;
    private volatile T instance;

    public SingletonCell(Supplier<T> factory) {
        this.factory = factory;
    }

    public T get() {
        throw new UnsupportedOperationException("TODO: double-checked locking around factory.get()");
    }
}
