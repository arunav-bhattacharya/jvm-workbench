package workbench.container.l03.app;

import workbench.container.l03.Component;

@Component
public class FxRates {
    public long toEurMinor(long amountMinor) { return amountMinor * 92 / 100; }
}
