package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class RemoteBookingClient implements BookingClient {
    private final BookingConfig config;

    public RemoteBookingClient(BookingConfig config) { this.config = config; }

    @Override
    public String reserve(String seat, long priceCents) { return "hold-" + seat; }

    @Override
    public String cancel(String holdId) { return "cancelled-" + holdId; }
}
