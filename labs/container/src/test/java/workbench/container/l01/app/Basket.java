package workbench.container.l01.app;

import workbench.container.l01.Component;
import workbench.container.l01.Scope;

/** One customer's basket: a fresh object for every customer, so it is a prototype. */
@Component(scope = Scope.PROTOTYPE)
public class Basket {
    private final PriceList prices;

    public Basket(PriceList prices) {
        this.prices = prices;
    }

    public PriceList prices() {
        return prices;
    }
}
