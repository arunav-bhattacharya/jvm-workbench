package workbench.executors.l06;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * Checkout for a shop that prices in EUR and charges in the customer's currency.
 *
 * <p>{@link #checkout} must return at once, without blocking the caller, and complete later:
 * <ol>
 *   <li>Fetch the EUR price and the EUR-to-{@code currency} rate <em>at the same time</em>,
 *       both on {@code io} (they are blocking calls).</li>
 *   <li>When both are ready, amount = price x rate, rounded to 2 decimals with
 *       {@code RoundingMode.HALF_EVEN}.</li>
 *   <li>Charge that amount with the gateway, which returns its own {@code CompletableFuture}.
 *       Don't block any thread waiting for it.</li>
 *   <li>Complete with a {@link Receipt}. If any step fails, the returned future fails, and later
 *       steps don't run (no charge without a price and a rate).</li>
 * </ol>
 */
public final class Checkout {
    private final PriceService prices;
    private final FxService fx;
    private final PaymentGateway gateway;
    private final Executor io;

    public Checkout(PriceService prices, FxService fx, PaymentGateway gateway, Executor io) {
        this.prices = prices;
        this.fx = fx;
        this.gateway = gateway;
        this.io = io;
    }

    public CompletableFuture<Receipt> checkout(String cartId, String currency) {
        throw new UnsupportedOperationException("TODO: supplyAsync x2, thenCombine, thenCompose the charge, thenApply the receipt");
    }
}
