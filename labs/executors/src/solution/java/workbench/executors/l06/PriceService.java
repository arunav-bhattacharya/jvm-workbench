package workbench.executors.l06;

import java.math.BigDecimal;

/** The cart service. Blocking: it makes an HTTP call and returns the cart total in EUR. */
public interface PriceService {
    BigDecimal priceEur(String cartId);
}
