package workbench.container.l03.app;

import workbench.container.l03.Component;

@Component
public class RemoteBookingClient implements BookingClient {
    private final BookingConfig config;
    private final BookingScript script;

    public RemoteBookingClient(BookingConfig config, BookingScript script) {
        this.config = config;
        this.script = script;
    }

    public BookingConfig config() { return config; }

    @Override
    public String reserve(String seat, long priceCents) {
        script.calls.incrementAndGet();
        if (script.failures.getAndDecrement() > 0) throw new BookingUnavailableException("booking service timed out");
        return "hold-" + seat + "-" + priceCents;
    }

    @Override
    public long listPriceCents(String seat) { return 12_000; }
}
