package workbench.jmm.l05;

import java.util.function.Supplier;

/**
 * A value computed on first use, at most once, no matter how many threads ask at the same time.
 *
 * <p>Write it with double-checked locking: a fast path that reads the field without a lock,
 * and a slow path that takes a lock, checks again, and runs the initializer. Make it correct
 * under the Java Memory Model, and let the initializer be garbage-collected once it has run.
 * You may assume the initializer never returns null.
 */
public final class DoubleCheckedLazy<T> implements Supplier<T> {

    public DoubleCheckedLazy(Supplier<? extends T> initializer) {
        throw new UnsupportedOperationException("TODO: keep the initializer");
    }

    @Override
    public T get() {
        throw new UnsupportedOperationException("TODO: fast path, then lock, check again, initialize once");
    }
}
