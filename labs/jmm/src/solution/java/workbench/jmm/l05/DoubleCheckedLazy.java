package workbench.jmm.l05;

import java.util.function.Supplier;

public final class DoubleCheckedLazy<T> implements Supplier<T> {
    // volatile: the fast path reads it with no lock, so the write must publish the value safely
    private volatile T value;
    // plain is fine: only read and cleared inside the lock
    private Supplier<? extends T> initializer;

    public DoubleCheckedLazy(Supplier<? extends T> initializer) {
        this.initializer = initializer;
    }

    @Override
    public T get() {
        T v = value;                      // 1. fast path: one volatile read
        if (v != null) return v;
        synchronized (this) {             // 2. slow path: one thread at a time
            v = value;                    // 3. check again: another thread may have won
            if (v == null) {
                v = initializer.get();    // 4. run the initializer exactly once
                value = v;                // 5. volatile write publishes the finished object
                initializer = null;       // 6. let the initializer and what it captured be collected
            }
            return v;
        }
    }
}
