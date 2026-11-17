package workbench.container.l03.demo.app;

import workbench.container.l03.Retry;
import workbench.container.l03.Timed;

/** The box office's link to the city's booking service. */
public interface BookingClient {
    @Timed
    @Retry(attempts = 3, on = BookingUnavailableException.class)
    String reserve(String seat, long priceCents);

    @Timed
    @Retry(attempts = 3, on = BookingUnavailableException.class)
    String cancel(String holdId);
}
