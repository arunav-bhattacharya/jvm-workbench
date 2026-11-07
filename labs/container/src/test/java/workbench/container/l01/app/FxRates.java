package workbench.container.l01.app;

import workbench.container.l01.Component;

@Component
public class FxRates {
    public long toEurMinor(long amountMinor, String currency) {
        return currency.equals("EUR") ? amountMinor : amountMinor * 92 / 100;
    }
}
