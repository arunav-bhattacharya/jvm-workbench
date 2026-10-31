package workbench.patterns.l04;

import java.math.BigDecimal;
import java.util.Currency;
import java.util.List;

/** The Java twin of ExtensionAdapters.kt. Java has no extension functions, so the adapter is a static method. */
public class ExtensionAdaptersJava {
    // a vendor DTO from the issuer SDK, with its names and units
    record VendorTxn(String txnRef, String amt, String ccyNum, String respCd) {}

    // our domain type
    record Receipt(String reference, long amountMinor, String currency, boolean approved) {}

    // callers write toReceipt(txn), not txn.toReceipt(); the mapping still lives in one place
    static Receipt toReceipt(VendorTxn txn) {
        Currency currency = Currency.getAvailableCurrencies().stream()
                .filter(c -> c.getNumericCode() == Integer.parseInt(txn.ccyNum()))
                .findFirst().orElseThrow();
        return new Receipt(
                txn.txnRef(),
                new BigDecimal(txn.amt()).movePointRight(currency.getDefaultFractionDigits()).longValueExact(),
                currency.getCurrencyCode(),
                txn.respCd().equals("00"));
    }

    public static void main(String[] args) {
        List<VendorTxn> fromSdk = List.of(
                new VendorTxn("T-1001", "12.50", "978", "00"),
                new VendorTxn("T-1002", "1250", "392", "00"),
                new VendorTxn("T-1003", "99.99", "840", "51"));
        fromSdk.stream().map(ExtensionAdaptersJava::toReceipt).forEach(System.out::println);
    }
}
