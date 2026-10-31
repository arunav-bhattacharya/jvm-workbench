package workbench.concurrency.l02;

import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;

public class OutboxRelay implements Runnable {
    private final Supplier<List<String>> outbox;
    private final Consumer<String> publisher;
    private final long idleMillis;

    public OutboxRelay(Supplier<List<String>> outbox, Consumer<String> publisher, long idleMillis) {
        this.outbox = outbox;
        this.publisher = publisher;
        this.idleMillis = idleMillis;
    }

    @Override
    public void run() {
        try {
            // 1. busy path: check the flag once per batch, so a busy relay still notices the request
            while (!Thread.currentThread().isInterrupted()) {
                List<String> batch = outbox.get();
                for (String message : batch) publisher.accept(message);   // finish the batch in hand
                if (batch.isEmpty()) {
                    Thread.sleep(idleMillis);   // 2. idle path: interrupt wakes sleep with an exception
                }
            }
            // the loop ended because the flag is set: it is still set, nothing to restore
        } catch (InterruptedException e) {
            // 3. sleep cleared the flag before throwing. Put it back so the thread's owner can see it.
            Thread.currentThread().interrupt();
        }
    }
}
