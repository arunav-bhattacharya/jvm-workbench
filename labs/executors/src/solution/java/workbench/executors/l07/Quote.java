package workbench.executors.l07;

import java.math.BigDecimal;

/** One supplier's price offer. */
public record Quote(String provider, BigDecimal price) {}
