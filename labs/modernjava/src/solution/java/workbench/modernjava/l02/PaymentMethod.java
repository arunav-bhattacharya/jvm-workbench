package workbench.modernjava.l02;

// sealed: only these four may implement PaymentMethod directly. With every subtype in this
// file, the permits clause could be left out and javac would infer the same list.
public sealed interface PaymentMethod
        permits PaymentMethod.Card, PaymentMethod.BankTransfer, PaymentMethod.Wallet, PaymentMethod.PartnerMethod {

    record Card(String network, String last4) implements PaymentMethod {}       // records are final

    // a sealed branch: closed to new kinds of transfer
    sealed interface BankTransfer extends PaymentMethod permits Sepa, Swift {}

    record Sepa(String iban) implements BankTransfer {}

    record Swift(String bic, String account) implements BankTransfer {}

    record Wallet(String provider) implements PaymentMethod {}

    // non-sealed: deliberately reopens this branch, so partner code may implement it
    non-sealed interface PartnerMethod extends PaymentMethod {
        String partnerId();

        int settlementDays();
    }
}
