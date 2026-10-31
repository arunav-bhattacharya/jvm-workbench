package workbench.patterns.l04;

/** Our port: the only way the payment code talks to any issuer. Given; don't edit. */
public interface CardAuthorizer {

    AuthResult authorize(String pan, long amountMinor, String currency);

    /** What an authorization can come back as, in our words, not the vendor's. */
    sealed interface AuthResult {
        record Approved(String authCode) implements AuthResult {}
        record Declined(String reason) implements AuthResult {}
        record Unavailable(String detail) implements AuthResult {}
    }
}
