package workbench.patterns.l04;

/**
 * Adapter: makes {@link LegacyIssuerSdk} look like our {@link CardAuthorizer} port.
 *
 * <p>Translate on the way in: minor units become a decimal string ({@link Amounts#toDecimal}) and the
 * currency code becomes its numeric code ({@link Amounts#numericCode}).
 *
 * <p>Translate on the way out: response "00|authId" is {@code Approved(authId)}; "51" is
 * {@code Declined("insufficient funds")}; "05" is {@code Declined("do not honor")}; any other code
 * {@code xx} is {@code Declined("issuer code xx")}. An {@link SdkException} becomes
 * {@code Unavailable(message of the exception)}. Nothing from the vendor (its exception, its response
 * string) may leak past this class.
 */
public final class IssuerSdkAdapter implements CardAuthorizer {
    private final LegacyIssuerSdk sdk;

    public IssuerSdkAdapter(LegacyIssuerSdk sdk) {
        this.sdk = sdk;
    }

    @Override
    public AuthResult authorize(String pan, long amountMinor, String currency) {
        throw new UnsupportedOperationException("TODO: convert the arguments, call sdk.auth, map the response and errors");
    }
}
