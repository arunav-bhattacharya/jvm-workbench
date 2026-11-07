package workbench.quotes.scratch;

import java.math.BigDecimal;

public record Q(String symbol, BigDecimal price, String provider, boolean stale) {}
