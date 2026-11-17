package workbench.container.l02.demo.app;

import workbench.container.l02.Component;

@Component
public class FlakyBooking implements BookingClient {
    private final BookingScript script;

    public FlakyBooking(BookingScript script) {
        this.script = script;
    }

    @Override
    public String reserve(String seat, long priceCents) {
        script.seen.add("reserve");
        return "hold-" + seat;
    }

    @Override
    public String confirm(String holdId) {
        if (script.confirmFailures.getAndDecrement() > 0) {
            script.seen.add("confirm (timed out)");
            throw new BookingUnavailableException("booking service timed out");
        }
        script.seen.add("confirm");
        return "ticket-" + holdId;
    }
}
