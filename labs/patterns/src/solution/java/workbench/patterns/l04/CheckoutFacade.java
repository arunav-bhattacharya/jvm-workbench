package workbench.patterns.l04;

import workbench.patterns.l04.CardAuthorizer.AuthResult;

public final class CheckoutFacade {

    public interface Ledger {
        void post(String orderId, long amountMinor, String currency, String authCode);
    }

    public interface Notifier {
        void send(String email, String message);
    }

    public sealed interface CheckoutResult {
        record Paid(String authCode) implements CheckoutResult {}
        record Declined(String reason) implements CheckoutResult {}
        record RetryLater() implements CheckoutResult {}
    }

    private final CardAuthorizer authorizer;
    private final Ledger ledger;
    private final Notifier notifier;

    public CheckoutFacade(CardAuthorizer authorizer, Ledger ledger, Notifier notifier) {
        this.authorizer = authorizer;
        this.ledger = ledger;
        this.notifier = notifier;
    }

    public CheckoutResult checkout(String orderId, String pan, long amountMinor, String currency, String email) {
        // the facade decides the order of the steps; callers make one call
        return switch (authorizer.authorize(pan, amountMinor, currency)) {
            case AuthResult.Approved ok -> {
                ledger.post(orderId, amountMinor, currency, ok.authCode());          // 1. the money moved: record it first
                notifyQuietly(email, "Paid " + Amounts.toDecimal(amountMinor, currency) + " " + currency
                        + " for order " + orderId);                                   // 2. a receipt is best effort
                yield new CheckoutResult.Paid(ok.authCode());
            }
            case AuthResult.Declined no -> {
                notifyQuietly(email, "Payment declined: " + no.reason());
                yield new CheckoutResult.Declined(no.reason());
            }
            case AuthResult.Unavailable down -> new CheckoutResult.RetryLater();      // 3. nothing happened: tell no one
        };
    }

    private void notifyQuietly(String email, String message) {
        try {
            notifier.send(email, message);
        } catch (RuntimeException e) {
            // a failed email must not turn an approved, posted payment into an error; log and move on
        }
    }
}
