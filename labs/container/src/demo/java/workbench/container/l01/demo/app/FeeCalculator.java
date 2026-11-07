package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class FeeCalculator {
    private final FxRates rates;

    public FeeCalculator(FxRates rates) { this.rates = rates; }

    public long feeMinor(long amountMinor) { return (rates.toEurMinor(amountMinor) * 29 + 500) / 1000; }
}
