package workbench.vthreads.l03;

import java.util.concurrent.Callable;

/**
 * Guards one scarce downstream resource (a card issuer API, a database) so that at most
 * {@code maxConcurrent} calls are inside it at once, however many threads call it.
 * Callers over the limit wait their turn.
 *
 * <p>Build it on a {@link java.util.concurrent.Semaphore}. Every caller of the resource
 * must share the same Bulkhead object.
 */
public final class Bulkhead {

    public Bulkhead(int maxConcurrent) {
        // TODO: create the semaphore
    }

    /** Waits for a free slot, runs {@code work}, and always gives the slot back, even if work throws. */
    public <T> T call(Callable<T> work) throws Exception {
        throw new UnsupportedOperationException("TODO: acquire, run, release in finally");
    }

    /** How many slots are free right now. */
    public int available() {
        throw new UnsupportedOperationException("TODO: ask the semaphore");
    }
}
