package workbench.quotes.l03;

import java.math.BigDecimal;

/**
 * One price for one currency pair from one provider. {@code stale} means it came from the cache
 * because no provider answered in time.
 */
public record Quote(String symbol, BigDecimal price, String provider, boolean stale) {

    public static Quote live(String symbol, String price, String provider) {
        return new Quote(symbol, new BigDecimal(price), provider, false);
    }

    public Quote asStale() {
        return new Quote(symbol, price, provider, true);
    }
}
