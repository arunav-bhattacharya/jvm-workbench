package workbench.concurrency.l09;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * Merchants register webhook listeners; every settled payment is published to all of them.
 * Listeners are added and removed rarely. {@link #publish} runs on every payment, from many threads.
 *
 * <p>This version keeps the listeners in an {@link ArrayList}. It throws
 * {@link java.util.ConcurrentModificationException} when a listener removes itself during
 * {@code publish} (one thread is enough), and it breaks when threads register while others publish.
 * Fix it by choosing the right collection from {@code java.util.concurrent}; you should not need a lock.
 */
public class WebhookRegistry {
    private final List<Consumer<String>> listeners = new ArrayList<>();

    public void register(Consumer<String> listener) {
        listeners.add(listener);
    }

    public void unregister(Consumer<String> listener) {
        listeners.remove(listener);
    }

    /** Sends {@code event} to every listener registered when the publish started. */
    public void publish(String event) {
        for (Consumer<String> l : listeners) {
            l.accept(event);
        }
    }

    public int count() {
        return listeners.size();
    }
}
