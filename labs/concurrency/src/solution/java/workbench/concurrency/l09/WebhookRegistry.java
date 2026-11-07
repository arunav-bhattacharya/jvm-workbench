package workbench.concurrency.l09;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

public class WebhookRegistry {
    // every add or remove copies the array; every iteration reads a snapshot that never changes.
    // Rare writes, constant reads: exactly the case CopyOnWriteArrayList is for.
    private final List<Consumer<String>> listeners = new CopyOnWriteArrayList<>();

    public void register(Consumer<String> listener) {
        listeners.add(listener);
    }

    public void unregister(Consumer<String> listener) {
        listeners.remove(listener);
    }

    public void publish(String event) {
        for (Consumer<String> l : listeners) {   // iterates the snapshot taken here: no CME, no lock
            l.accept(event);
        }
    }

    public int count() {
        return listeners.size();
    }
}
