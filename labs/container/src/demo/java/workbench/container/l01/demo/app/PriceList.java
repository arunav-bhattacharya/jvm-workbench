package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class PriceList {
    private final SeatingPlan plan;

    public PriceList(SeatingPlan plan) { this.plan = plan; }

    public long priceCents(String seat) { return plan.isStalls(seat) ? 12_000 : 8_000; }

    public long feeCents(long priceCents) { return (priceCents * 29 + 500) / 1000; }   // a 2.9% booking fee
}
