package workbench.executors.l06;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

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
        // 1. start both blocking calls now, on the IO pool, so they run side by side
        CompletableFuture<BigDecimal> price = CompletableFuture.supplyAsync(() -> prices.priceEur(cartId), io);
        CompletableFuture<BigDecimal> rate = CompletableFuture.supplyAsync(() -> fx.rate("EUR", currency), io);

        return price
                // 2. when both are done, combine them (runs on whichever thread finished second)
                .thenCombine(rate, (p, r) -> p.multiply(r).setScale(2, RoundingMode.HALF_EVEN))
                // 3. the gateway returns a future: thenCompose flattens it instead of nesting it
                .thenCompose(amount -> gateway.charge(cartId, amount, currency)
                        // 4. build the receipt from the amount and the charge id
                        .thenApply(chargeId -> new Receipt(cartId, amount, currency, chargeId)));
    }
}
