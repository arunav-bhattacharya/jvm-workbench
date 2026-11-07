package workbench.memory.l03;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Stands in for a native library (a card-terminal SDK, a compression codec): it hands out handles
 * to memory outside the heap, and every handle must come back to {@link #free} exactly once.
 * You don't need to change this class.
 */
public final class NativeMemory {
    private final AtomicLong nextHandle = new AtomicLong(1);
    private final Set<Long> open = ConcurrentHashMap.newKeySet();
    private final AtomicInteger frees = new AtomicInteger();

    /** Reserves {@code bytes} of native memory and returns its handle. */
    public long allocate(int bytes) {
        long handle = nextHandle.getAndIncrement();
        open.add(handle);
        return handle;
    }

    /** Gives a handle back. Freeing a handle twice is a crash in real native code; here it throws. */
    public void free(long handle) {
        if (!open.remove(handle)) throw new IllegalStateException("double free of handle " + handle);
        frees.incrementAndGet();
    }

    /** Handles allocated and not yet freed. */
    public int openHandles() { return open.size(); }

    /** How many times {@link #free} succeeded. */
    public int frees() { return frees.get(); }
}
