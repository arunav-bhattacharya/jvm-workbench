package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class RemoteBookingClient implements BookingClient {
    private final BookingConfig config;

    public RemoteBookingClient(BookingConfig config) { this.config = config; }

    @Override
    public String reserve(String seat, long priceCents) {
        return "hold-" + seat + "@" + config.address();
    }
}
