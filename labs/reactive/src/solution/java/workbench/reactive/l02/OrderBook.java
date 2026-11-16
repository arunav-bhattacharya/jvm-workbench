package workbench.reactive.l02;

/**
 * A blocking client for the bakery's order book, which lives in another program.
 * Each call is a slow round trip over the network, so every extra call costs the customer time.
 */
public interface OrderBook {
    /** Returns the order's status, such as "READY", or null if the order book doesn't know the order. */
    String fetchStatus(String orderId);
}
