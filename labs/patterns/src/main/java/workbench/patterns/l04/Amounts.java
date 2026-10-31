package workbench.patterns.l04;

import java.math.BigDecimal;
import java.util.Currency;

/** Money helpers. Given; you don't need to change them. */
public final class Amounts {
    private Amounts() {}

    /** 1250 EUR is "12.50", 5 EUR is "0.05", 1250 JPY is "1250" (the yen has no minor unit). */
    public static String toDecimal(long amountMinor, String currency) {
        int digits = Currency.getInstance(currency).getDefaultFractionDigits();
        return BigDecimal.valueOf(amountMinor, digits).toPlainString();
    }

    /** "EUR" is "978", "JPY" is "392". */
    public static String numericCode(String currency) {
        return Currency.getInstance(currency).getNumericCodeAsString();
    }
}
