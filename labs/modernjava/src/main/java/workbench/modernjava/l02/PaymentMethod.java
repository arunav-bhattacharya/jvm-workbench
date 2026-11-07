package workbench.modernjava.l02;

/**
 * How a customer pays. The payments team owns this list: settlement code must handle every
 * method on it. The one exception is {@link PartnerMethod}, which partner teams implement in
 * their own code, outside this file.
 *
 * <p>Right now anyone can implement any of these interfaces, so the compiler can't check that
 * a switch over a payment method is complete.
 *
 * <p>TODO 1: seal {@code PaymentMethod} so its direct subtypes are exactly {@code Card},
 * {@code BankTransfer}, {@code Wallet} and {@code PartnerMethod}.
 * <br>TODO 2: seal {@code BankTransfer} so its only subtypes are {@code Sepa} and {@code Swift}.
 * <br>TODO 3: leave {@code PartnerMethod} open to partner code. Every subtype of a sealed type
 * needs one of {@code final}, {@code sealed} or {@code non-sealed}: which one fits here?
 * The records need nothing: a record is already final.
 */
public interface PaymentMethod {

    record Card(String network, String last4) implements PaymentMethod {}

    interface BankTransfer extends PaymentMethod {}

    record Sepa(String iban) implements BankTransfer {}

    record Swift(String bic, String account) implements BankTransfer {}

    record Wallet(String provider) implements PaymentMethod {}

    /** Implemented by partner teams. */
    interface PartnerMethod extends PaymentMethod {
        String partnerId();

        int settlementDays();
    }
}
