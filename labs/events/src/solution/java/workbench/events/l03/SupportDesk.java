package workbench.events.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * The support team's view of the day, written in Java against the Kotlin event library: how many
 * times each parcel failed to arrive (they phone the receiver after the second try), and the total
 * weight delivered. Closing it removes every subscription it made.
 */
public final class SupportDesk implements AutoCloseable {
    private final Map<String, Integer> failedAttempts = new ConcurrentHashMap<>();
    private final AtomicLong deliveredGrams = new AtomicLong();
    private final Subscription subscriptions;

    public SupportDesk(EventBus bus) {
        // a handler of any event: Handler is `in`, so Java sees on(Class<E>, Handler<? super E>)
        Handler<ParcelEvent> countAttempt = event -> failedAttempts.merge(Events.parcelId(event), 1, Integer::sum);

        // one block, one handle; a Consumer, so no `return Unit.INSTANCE`
        this.subscriptions = Events.subscriptions(bus, b -> {
            b.on(ParcelDelivered.class, d -> deliveredGrams.addAndGet(Events.grams(d)));
            b.on(DeliveryFailed.class, countAttempt);
        });
    }

    /** How many delivery attempts failed for one parcel. */
    public int failedAttempts(String parcelId) {
        return failedAttempts.getOrDefault(parcelId, 0);
    }

    /** The total weight delivered, in grams. */
    public long deliveredGrams() {
        return deliveredGrams.get();
    }

    @Override
    public void close() {
        subscriptions.close();          // Subscription.close() throws nothing, so no try/catch here
    }
}
