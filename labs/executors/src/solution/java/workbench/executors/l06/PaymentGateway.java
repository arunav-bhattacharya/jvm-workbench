package workbench.executors.l06;

import java.math.BigDecimal;
import java.util.concurrent.CompletableFuture;

/** The payment gateway client. Already asynchronous: the future completes with a charge id. */
public interface PaymentGateway {
    CompletableFuture<String> charge(String cartId, BigDecimal amount, String currency);
}
