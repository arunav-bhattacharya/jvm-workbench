package workbench.container.l03.app;

import workbench.container.l03.Component;

@Component
public class PriceList {
    private final SeatingPlan plan;

    public PriceList(SeatingPlan plan) { this.plan = plan; }

    public SeatingPlan plan() { return plan; }

    public long feeCents(long priceCents) { return (priceCents * 29 + 500) / 1000; }
}
