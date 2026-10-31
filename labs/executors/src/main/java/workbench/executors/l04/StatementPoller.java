package workbench.executors.l04;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Polls the bank for new statement lines until it is told to stop. It runs as a task on an
 * executor, and the executor stops it with {@code shutdownNow()} or {@code future.cancel(true)},
 * both of which interrupt the thread.
 *
 * <p>BUG: it never stops. {@code shutdownNow()} returns, {@code awaitTermination} times out, and
 * the poller keeps calling the bank. The loop condition looks right. Find what defeats it and
 * fix it, without changing the public methods.
 */
public final class StatementPoller implements Runnable {
    private final Runnable pollOnce;
    private final Duration interval;
    private final AtomicInteger polls = new AtomicInteger();

    public StatementPoller(Runnable pollOnce, Duration interval) {
        this.pollOnce = pollOnce;
        this.interval = interval;
    }

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            pollOnce.run();
            polls.incrementAndGet();
            pause();
        }
    }

    private void pause() {
        try {
            Thread.sleep(interval.toMillis());
        } catch (InterruptedException e) {
            // nothing useful to do here; the loop will carry on
        }
    }

    /** How many times the bank has been polled. */
    public int polls() {
        return polls.get();
    }
}
