package workbench.container.l03.app;

import workbench.container.l03.Retry;
import workbench.container.l03.Timed;

public interface BookingClient {
    @Timed
    @Retry(attempts = 3, on = BookingUnavailableException.class)
    String reserve(String seat, long priceCents);

    /** Not intercepted: forwarded as it is. */
    long listPriceCents(String seat);

    /** Student seats cost at most 50.00. A default method: its call to reserve goes through the proxy. */
    default String reserveStudentSeat(String seat) {
        return reserve(seat, Math.min(listPriceCents(seat), 5_000));
    }
}
