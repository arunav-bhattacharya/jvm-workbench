package workbench.bytecode.l04;

/** The card issuer's API, as the payments service sees it. */
public interface CardIssuerClient {
    /** Returns an authorization id such as {@code "auth-1111"}. */
    String authorize(String pan, long amountMinor) throws IssuerUnavailableException;

    /** Captures an authorization and returns {@code "captured " + authId}. */
    String capture(String authId) throws IssuerUnavailableException;

    /** A default method: two calls on {@code this}. */
    default String authorizeAndCapture(String pan, long amountMinor) throws IssuerUnavailableException {
        return capture(authorize(pan, amountMinor));
    }

    /** Thrown when the issuer can't be reached. Checked, and declared by every method. Worth a retry. */
    class IssuerUnavailableException extends Exception {
        public IssuerUnavailableException(String message) { super(message); }
    }

    /** The issuer said no. Retrying won't change its mind. */
    class CardDeclinedException extends RuntimeException {
        public CardDeclinedException(String message) { super(message); }
    }
}
