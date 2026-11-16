package workbench.executors.l07;

import java.math.BigDecimal;

/** One supplier's price service. Blocking: it calls a web service, which may be slow or throw. */
public interface QuoteProvider {
    String name();

    /** Today's price of one unit of {@code item}, such as "flour" (a sack of flour). */
    BigDecimal quote(String item);
}
