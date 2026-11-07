package workbench.executors.l07;

import java.math.BigDecimal;

/** One FX quote provider. Blocking: it makes an HTTP call and may be slow or throw. */
public interface QuoteProvider {
    String name();

    /** The price of one unit of the base currency in the quote currency, for a pair like "EUR/USD". */
    BigDecimal quote(String pair);
}
