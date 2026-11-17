package workbench.container.l03.app;

import workbench.container.l03.Component;

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

    public BookingClient booking() { return booking; }
    public PriceList prices() { return prices; }
    public SalesBook book() { return book; }

    public String sell(String seat, long priceCents) {
        String hold = booking.reserve(seat, priceCents);
        book.add(hold + " fee=" + prices.feeCents(priceCents));
        return hold;
    }
}
