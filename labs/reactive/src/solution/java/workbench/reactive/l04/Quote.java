package workbench.reactive.l04;

import java.math.BigDecimal;

/** A quote for a cake order, built from three independent lookups. */
public record Quote(BigDecimal price, BigDecimal deliveryFee, BigDecimal taxRate) {
}
