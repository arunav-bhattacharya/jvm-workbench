package workbench.container.l03.app;

import workbench.container.l03.Component;
import workbench.container.l03.Scope;

@Component(scope = Scope.PROTOTYPE)
public class Basket {
    private final PriceList prices;

    public Basket(PriceList prices) { this.prices = prices; }

    public PriceList prices() { return prices; }
}
