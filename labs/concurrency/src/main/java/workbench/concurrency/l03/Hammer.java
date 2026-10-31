package workbench.concurrency.l03;

/**
 * A tiny harness that makes threads collide on purpose.
 *
 * <p>Write {@link #run}: start {@code threads} threads, hold them all behind one
 * {@link java.util.concurrent.CountDownLatch} until every thread is ready, release
 * them together, then wait for all of them to finish.
 */
public final class Hammer {
    private Hammer() {}

    /**
     * Runs {@code task} once on each of {@code threads} new threads, all released at the same moment.
     * Returns only after every thread has finished.
     */
    public static void run(int threads, Runnable task) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: start the threads behind a latch, release them, join them");
    }
}
