package workbench.performance.l05;

/**
 * Authorizes payments by asking the issuer. It works, but nobody can see how long the issuer takes
 * or which merchants get declined.
 *
 * <p>TODO: record one {@link AuthorizationEvent} per call. Start timing just before the issuer call,
 * stop just after it, fill in the fields, and commit. Keep the return value as it is.
 */
public final class Authorizer {
    private final Issuer issuer;

    public Authorizer(Issuer issuer) {
        this.issuer = issuer;
    }

    public boolean authorize(String merchant, long amountCents) {
        return issuer.approve(merchant, amountCents);
    }
}
