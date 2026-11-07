package workbench.memory.l03;

import java.lang.ref.Cleaner;

/**
 * A buffer backed by native memory. Callers should close it with try-with-resources. If one forgets,
 * a {@link Cleaner} must free the memory after the buffer becomes unreachable.
 *
 * <p>This version has two bugs. A second {@code close()} frees the handle twice. And a buffer that is
 * never closed is never cleaned at all. Find out why, then fix both.
 */
public final class NativeBuffer implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();   // one cleaner thread for every buffer

    private final NativeMemory memory;
    private final long handle;

    public NativeBuffer(NativeMemory memory, int bytes) {
        this.memory = memory;
        this.handle = memory.allocate(bytes);
        CLEANER.register(this, () -> memory.free(handle));     // the safety net
    }

    public long handle() {
        return handle;
    }

    @Override
    public void close() {
        memory.free(handle);
    }
}
