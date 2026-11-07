package workbench.memory.l03;

import java.lang.ref.Cleaner;

public final class NativeBuffer implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();   // one cleaner thread for every buffer

    private final long handle;
    private final Cleaner.Cleanable cleanable;

    public NativeBuffer(NativeMemory memory, int bytes) {
        this.handle = memory.allocate(bytes);
        // The action holds only what it needs to free the memory. The old lambda read the field
        // `handle`, which means `this.handle`, so it held the buffer and the buffer could never
        // become phantom reachable.
        this.cleanable = CLEANER.register(this, new Release(memory, handle));
    }

    // static: a non-static nested class or a lambda that touches a field would hold `this`
    private static final class Release implements Runnable {
        private final NativeMemory memory;
        private final long handle;

        Release(NativeMemory memory, long handle) {
            this.memory = memory;
            this.handle = handle;
        }

        @Override
        public void run() {
            memory.free(handle);
        }
    }

    public long handle() {
        return handle;
    }

    @Override
    public void close() {
        cleanable.clean();   // runs Release at most once and unregisters it, so the cleaner won't run it again
    }
}
