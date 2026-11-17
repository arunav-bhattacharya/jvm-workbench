package workbench.patterns.l04;

import workbench.patterns.l04.Warehouse.StockResult;

/**
 * Facade: one call to place an order, so the website, the phone line or the shop counter never has
 * to know the order of warehouse, order book and notifier calls.
 *
 * <p>{@link #place} must:
 * <ul>
 *   <li>reserve the stock;</li>
 *   <li>on {@code Reserved}: write the order in the order book (orderId, product, grams, hold id),
 *       then send the confirmation "Order o-1: 1.250 kg of FLOUR is on its way" (use
 *       {@link Units#toKilos}), and return {@code Placed(holdId)}. A notifier that throws must not
 *       undo or fail an order that was reserved and written down;</li>
 *   <li>on {@code Refused}: write nothing, send "Sorry, order o-1 failed: " + reason, return
 *       {@code Refused(reason)};</li>
 *   <li>on {@code Unavailable}: write nothing, send nothing, return {@code RetryLater}.</li>
 * </ul>
 * Keep it orchestration only: no unit maths, no warehouse codes.
 */
public final class OrderDesk {

    public interface OrderBook {
        void record(String orderId, String product, long grams, String holdId);
    }

    public interface Notifier {
        void send(String email, String message);
    }

    public sealed interface OrderResult {
        record Placed(String holdId) implements OrderResult {}
        record Refused(String reason) implements OrderResult {}
        record RetryLater() implements OrderResult {}
    }

    private final Warehouse warehouse;
    private final OrderBook orderBook;
    private final Notifier notifier;

    public OrderDesk(Warehouse warehouse, OrderBook orderBook, Notifier notifier) {
        this.warehouse = warehouse;
        this.orderBook = orderBook;
        this.notifier = notifier;
    }

    public OrderResult place(String orderId, String product, long grams, String email) {
        throw new UnsupportedOperationException("TODO: reserve, then record and notify depending on the result");
    }
}
