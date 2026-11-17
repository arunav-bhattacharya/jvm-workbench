package workbench.container.l02.demo.app;

import workbench.container.l02.Retry;
import workbench.container.l02.Timed;

/** The box office's link to the city's booking service. */
public interface BookingClient {
    @Timed
    @Retry(attempts = 3, on = BookingUnavailableException.class)
    String reserve(String seat, long priceCents);

    @Timed
    @Retry(attempts = 3, on = BookingUnavailableException.class)
    String confirm(String holdId);

    /** Two booking calls in one default method. */
    default String reserveAndConfirm(String seat, long priceCents) {
        return confirm(reserve(seat, priceCents));
    }
}
