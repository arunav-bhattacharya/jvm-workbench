package workbench.patterns.l04;

/**
 * A pretend vendor SDK from a card issuer. You can't change it. Its shape is typical of old SDKs:
 * amounts as decimal strings, currency as an ISO 4217 numeric code, results packed into a string,
 * and a checked exception for anything that goes wrong on the wire. Given; don't edit.
 */
public class LegacyIssuerSdk {

    /**
     * Sends an authorization request.
     *
     * @param pan             card number, digits only
     * @param amount          amount in major units as a plain decimal string, such as "12.50"
     * @param currencyNumeric ISO 4217 numeric code, such as "978" for EUR
     * @return "responseCode|authId", for example "00|A1111" (approved) or "51|" (insufficient funds)
     * @throws SdkException when the issuer can't be reached
     */
    public String auth(String pan, String amount, String currencyNumeric) throws SdkException {
        // the sandbox approves anything under 1,000.00 and declines the rest with 51
        boolean small = new java.math.BigDecimal(amount).compareTo(new java.math.BigDecimal("1000")) < 0;
        return small ? "00|A" + pan.substring(pan.length() - 4) : "51|";
    }
}
