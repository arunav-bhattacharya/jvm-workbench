package workbench.patterns.l04;

public final class IssuerSdkAdapter implements CardAuthorizer {
    private final LegacyIssuerSdk sdk;

    public IssuerSdkAdapter(LegacyIssuerSdk sdk) {
        this.sdk = sdk;
    }

    @Override
    public AuthResult authorize(String pan, long amountMinor, String currency) {
        String raw;
        try {
            // 1. translate our types into the vendor's on the way in
            raw = sdk.auth(pan, Amounts.toDecimal(amountMinor, currency), Amounts.numericCode(currency));
        } catch (SdkException e) {
            // 2. the vendor's checked exception stops here and becomes one of our results
            return new AuthResult.Unavailable(e.getMessage());
        }
        // 3. translate the vendor's packed string into our sealed result on the way out
        String[] parts = raw.split("\\|", -1);
        String code = parts[0];
        return switch (code) {
            case "00" -> new AuthResult.Approved(parts.length > 1 ? parts[1] : "");
            case "51" -> new AuthResult.Declined("insufficient funds");
            case "05" -> new AuthResult.Declined("do not honor");
            default -> new AuthResult.Declined("issuer code " + code);
        };
    }
}
