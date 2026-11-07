package workbench.container.l01.app;

import workbench.container.l01.Component;

@Component
public class FeeCalculator {
    private final FxRates rates;

    public FeeCalculator(FxRates rates) {
        this.rates = rates;
    }

    public FxRates rates() {
        return rates;
    }

    public long feeMinor(long amountMinor) {
        return (amountMinor * 29 + 500) / 1000;
    }
}
