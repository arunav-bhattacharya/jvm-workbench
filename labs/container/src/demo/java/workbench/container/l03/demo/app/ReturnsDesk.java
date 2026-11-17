package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class ReturnsDesk {
    private final BookingClient booking;
    private final SalesBook book;

    public ReturnsDesk(BookingClient booking, SalesBook book) {
        this.booking = booking;
        this.book = book;
    }

    public String takeBack(String holdId) {
        String cancelled = booking.cancel(holdId);
        book.add(cancelled);
        return cancelled;
    }
}
