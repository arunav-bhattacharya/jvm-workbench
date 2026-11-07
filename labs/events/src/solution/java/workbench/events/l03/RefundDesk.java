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

    public RefundDesk(EventBus bus) {
        // a handler of any event: Handler is `in`, so Java sees on(Class<E>, Handler<? super E>)
        Handler<PaymentEvent> countDecline = event -> declines.incrementAndGet();

        // one block, one handle; a Consumer, so no `return Unit.INSTANCE`
        this.subscriptions = Events.subscriptions(bus, b -> {
            b.on(PaymentRefunded.class, r -> refundedMinor.merge(Events.paymentId(r), Events.amountMinor(r), Long::sum));
            b.on(PaymentDeclined.class, countDecline);
        });
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
