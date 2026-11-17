package workbench.quotes.l02;

import java.math.BigDecimal;

/**
 * One price for sending a parcel to one destination, from one courier. {@code stale} means it
 * came from the cache because no courier answered in time.
 */
public record Quote(String destination, BigDecimal price, String provider, boolean stale) {

    public static Quote live(String destination, String price, String provider) {
        return new Quote(destination, new BigDecimal(price), provider, false);
    }

    public Quote asStale() {
        return new Quote(destination, price, provider, true);
    }
}
