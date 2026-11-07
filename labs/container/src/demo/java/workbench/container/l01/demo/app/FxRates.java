package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class FxRates {
    public long toEurMinor(long amountMinor) { return amountMinor * 92 / 100; }
}
