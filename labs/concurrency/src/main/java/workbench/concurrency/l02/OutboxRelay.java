package workbench.concurrency.l02;

import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;

/**
 * Moves messages from a transactional outbox to Kafka, on its own thread.
 *
 * <p>The loop fetches a batch and publishes every message in it. When the outbox is empty
 * it sleeps for {@code idleMillis} before polling again.
 *
 * <p>This version never stops: its owner calls {@code interrupt()} on shutdown and nothing happens.
 * Fix {@link #run} so that it follows the interruption protocol:
 * <ul>
 *   <li>It stops soon after its thread is interrupted, whether it is sleeping or busy publishing.</li>
 *   <li>It finishes the batch in hand before stopping, so a batch is never half-published.</li>
 *   <li>When {@code run()} returns because of an interrupt, the thread's interrupt flag is still set.</li>
 * </ul>
 */
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
        while (true) {
            List<String> batch = outbox.get();
            for (String message : batch) publisher.accept(message);
            if (batch.isEmpty()) {
                try {
                    Thread.sleep(idleMillis);
                } catch (InterruptedException e) {
                    // "handled": logged and ignored. The flag was cleared when the exception was thrown.
                    System.err.println("relay interrupted, carrying on");
                }
            }
        }
    }
}
