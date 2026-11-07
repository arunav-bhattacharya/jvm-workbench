package workbench.modernjava.l02.demo;

/** Each branch of a sealed hierarchy ends as final, sealed or non-sealed. */
public class NonSealedDemo {

    sealed interface PaymentMethod permits Card, BankTransfer, PartnerMethod {}

    record Card(String network) implements PaymentMethod {}                     // final: a leaf

    sealed interface BankTransfer extends PaymentMethod permits Sepa, Swift {}  // sealed: closed below

    record Sepa(String iban) implements BankTransfer {}

    record Swift(String bic) implements BankTransfer {}

    non-sealed interface PartnerMethod extends PaymentMethod {                  // non-sealed: open below
        String partnerId();
    }

    // partner code: allowed, because PartnerMethod is non-sealed
    record GiftCard(String partnerId, String code) implements PartnerMethod {}

    // Step 3: delete "abstract" here and compile.
    sealed abstract static class Fee permits Flat, Percent {}

    static final class Flat extends Fee {
        final long minor;
        Flat(long minor) { this.minor = minor; }
    }

    static final class Percent extends Fee {
        final int basisPoints;
        Percent(int basisPoints) { this.basisPoints = basisPoints; }
    }

    static String describe(PaymentMethod m) {
        return switch (m) {
            case Card c -> "card " + c.network();
            case BankTransfer t -> "bank transfer " + t;          // one case for the sealed branch
            case PartnerMethod p -> "partner " + p.partnerId();   // one case for the open branch
        };
    }

    static long fee(Fee f, long amountMinor) {
        return switch (f) {
            case Flat flat -> flat.minor;
            case Percent pct -> amountMinor * pct.basisPoints / 10_000;
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Card("VISA")));
        System.out.println(describe(new Sepa("DE89370400440532013000")));
        System.out.println(describe(new GiftCard("giftly", "GC-7731")));
        System.out.println("PartnerMethod.isSealed(): " + PartnerMethod.class.isSealed());
        System.out.println("fee: " + fee(new Percent(290), 10_000) + " and " + fee(new Flat(35), 10_000));
    }
}
