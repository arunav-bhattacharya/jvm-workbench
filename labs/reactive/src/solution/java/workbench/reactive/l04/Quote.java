package workbench.reactive.l04;

import java.math.BigDecimal;

/** A checkout quote built from three independent lookups. */
public record Quote(BigDecimal fxRate, BigDecimal fee, BigDecimal limit) {
}
