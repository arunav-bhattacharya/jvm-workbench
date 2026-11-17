package workbench.patterns.l04;

import workbench.patterns.l04.Warehouse.StockResult;

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
        // the facade decides the order of the steps; callers make one call
        return switch (warehouse.reserve(product, grams)) {
            case StockResult.Reserved ok -> {
                orderBook.record(orderId, product, grams, ok.holdId());               // 1. the stock is set aside: write it down first
                notifyQuietly(email, "Order " + orderId + ": " + Units.toKilos(grams) + " kg of " + product
                        + " is on its way");                                          // 2. a confirmation is best effort
                yield new OrderResult.Placed(ok.holdId());
            }
            case StockResult.Refused no -> {
                notifyQuietly(email, "Sorry, order " + orderId + " failed: " + no.reason());
                yield new OrderResult.Refused(no.reason());
            }
            case StockResult.Unavailable down -> new OrderResult.RetryLater();        // 3. nothing happened: tell no one
        };
    }

    private void notifyQuietly(String email, String message) {
        try {
            notifier.send(email, message);
        } catch (RuntimeException e) {
            // a failed email must not turn a placed, written-down order into an error; log and move on
        }
    }
}
