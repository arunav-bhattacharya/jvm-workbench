package workbench.patterns.l04;

import workbench.patterns.l04.CardAuthorizer.AuthResult;

/**
 * Facade: one call for the whole checkout, so a REST resource or a Kafka consumer never has to know
 * the order of authorizer, ledger and notifier calls.
 *
 * <p>{@link #checkout} must:
 * <ul>
 *   <li>authorize the card;</li>
 *   <li>on {@code Approved}: post to the ledger (orderId, amount, currency, auth code), then send the
 *       receipt "Paid 12.50 EUR for order o-1" (use {@link Amounts#toDecimal}), and return
 *       {@code Paid(authCode)}. A notifier that throws must not undo or fail a payment that was
 *       approved and posted;</li>
 *   <li>on {@code Declined}: post nothing, send "Payment declined: " + reason, return {@code Declined(reason)};</li>
 *   <li>on {@code Unavailable}: post nothing, send nothing, return {@code RetryLater}.</li>
 * </ul>
 * Keep it orchestration only: no amount maths, no vendor codes.
 */
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
        throw new UnsupportedOperationException("TODO: authorize, then post and notify depending on the result");
    }
}
