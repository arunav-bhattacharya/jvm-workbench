package workbench.events.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * The support team's view of refunds and declines, written in Java against the Kotlin event library.
 * Closing it removes every subscription it made.
 */
public final class RefundDesk implements AutoCloseable {
    private final Map<String, Long> refundedMinor = new ConcurrentHashMap<>();
    private final AtomicInteger declines = new AtomicInteger();
    private final Subscription subscriptions;

    /**
     * TODO 7: in ONE Events.subscriptions(bus, b -> { ... }) block,
     *  - on PaymentRefunded: add Events.amountMinor(r) to refundedMinor under Events.paymentId(r)
     *    (Map.merge with Long::sum)
     *  - on PaymentDeclined: use a Handler<PaymentEvent> that increments declines. It should compile
     *    as it is: why?
     * and keep the returned Subscription in `subscriptions`.
     */
    public RefundDesk(EventBus bus) {
        throw new UnsupportedOperationException("TODO: subscribe to refunds and declines through Events.subscriptions");
    }

    /** Total refunded for one payment, in euro cents. */
    public long refundedMinor(String paymentId) {
        return refundedMinor.getOrDefault(paymentId, 0L);
    }

    public int declines() {
        return declines.get();
    }

    @Override
    public void close() {
        subscriptions.close();          // Subscription.close() throws nothing, so no try/catch here
    }
}
