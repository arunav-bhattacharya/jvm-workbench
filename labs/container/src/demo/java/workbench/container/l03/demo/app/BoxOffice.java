package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class BoxOffice {
    private final BookingClient booking;
    private final PriceList prices;
    private final TicketRules rules;
    private final SalesBook book;

    public BoxOffice(BookingClient booking, PriceList prices, TicketRules rules, SalesBook book) {
        this.booking = booking;
        this.prices = prices;
        this.rules = rules;
        this.book = book;
    }

    public String sell(String customerId, String seat, long priceCents) {
        if (!rules.allow(customerId, priceCents)) return "refused";
        String hold = booking.reserve(seat, priceCents);
        book.add(hold + " fee=" + prices.feeCents(priceCents));
        return hold;
    }
}
