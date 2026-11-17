package workbench.container.l03.demo.app;

import workbench.container.l03.Component;
import workbench.container.l03.Scope;

@Component(scope = Scope.PROTOTYPE)
public class Basket {
    private final PriceList prices;

    public Basket(PriceList prices) { this.prices = prices; }

    public long feeCents(long priceCents) { return prices.feeCents(priceCents); }
}
