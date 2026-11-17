package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class BoxOffice {
    private final BookingClient booking;
    private final PriceList prices;
    private final SalesBook book;

    public BoxOffice(BookingClient booking, PriceList prices, SalesBook book) {
        this.booking = booking;
        this.prices = prices;
        this.book = book;
    }

    public void sell(String seat, long priceCents) {
        book.add(booking.reserve(seat, priceCents) + " fee=" + prices.feeCents(priceCents));
    }
}
