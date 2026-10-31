package workbench.executors.l04;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

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
        while (!Thread.currentThread().isInterrupted()) {   // this check only works if nobody clears the flag
            pollOnce.run();
            polls.incrementAndGet();
            pause();
        }
    }

    private void pause() {
        try {
            Thread.sleep(interval.toMillis());
        } catch (InterruptedException e) {
            // throwing InterruptedException cleared the flag; set it again so the loop sees the request
            Thread.currentThread().interrupt();
        }
    }

    public int polls() {
        return polls.get();
    }
}
