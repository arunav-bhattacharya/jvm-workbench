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
        /*
         * TODO 7: in ONE Events.subscriptions(bus, b -> { ... }) block,
         *  - on ParcelDelivered: add Events.grams(d) to deliveredGrams
         *  - on DeliveryFailed: use a Handler<ParcelEvent> that adds 1 to failedAttempts under
         *    Events.parcelId(event) (Map.merge with Integer::sum). It should compile as it is: why?
         * and keep the returned Subscription in `subscriptions`.
         */
        throw new UnsupportedOperationException("TODO: subscribe to deliveries and failures through Events.subscriptions");
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
