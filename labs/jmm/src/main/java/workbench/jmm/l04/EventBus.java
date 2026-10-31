package workbench.jmm.l04;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/**
 * A tiny in-process event bus. Like a compacted Kafka topic, it remembers the last event and
 * replays it to every new listener as soon as the listener registers. (Given; not part of the exercise.)
 */
public final class EventBus {
    private final List<Consumer<PaymentEvent>> listeners = new CopyOnWriteArrayList<>();
    private volatile PaymentEvent last;

    public void register(Consumer<PaymentEvent> listener) {
        listeners.add(listener);
        PaymentEvent replay = last;
        if (replay != null) listener.accept(replay);   // the new listener hears the last event at once
    }

    public void publish(PaymentEvent event) {
        last = event;
        for (Consumer<PaymentEvent> l : listeners) l.accept(event);
    }
}
