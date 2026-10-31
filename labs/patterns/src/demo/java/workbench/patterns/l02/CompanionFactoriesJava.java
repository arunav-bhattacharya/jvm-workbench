package workbench.patterns.l02;

import java.util.List;

/** The Java twin of CompanionFactories.kt: static factories, a cached instance, and a sealed result. */
public class CompanionFactoriesJava {

    static final class Iban {
        final String country, digits;
        private Iban(String country, String digits) { this.country = country; this.digits = digits; }
        @Override public String toString() { return country + "****" + digits.substring(digits.length() - 4); }

        // 1. a named static factory: Iban.parse("...")
        static IbanResult parse(String raw) {
            String s = raw.replace(" ", "").toUpperCase();
            if (s.length() < 15) return new TooShort(s.length());
            if (!Character.isLetter(s.charAt(0)) || !Character.isLetter(s.charAt(1))) return new BadCountry(s.substring(0, 2));
            return new Ok(new Iban(s.substring(0, 2), s.substring(2)));
        }
    }

    sealed interface IbanResult {}                     // permitted subtypes: the records in this file
    record Ok(Iban iban) implements IbanResult {}
    record TooShort(int length) implements IbanResult {}
    record BadCountry(String prefix) implements IbanResult {}

    static final class Fee {
        private static final Fee STANDARD = new Fee(290);
        final int bps;
        private Fee(int bps) { this.bps = bps; }
        // 2. Java has no operator invoke, so the cached-instance factory needs a name
        static Fee of(int bps) { return bps == 290 ? STANDARD : new Fee(bps); }
    }

    interface Ledger {
        void post(String entry);
        // 3. a static factory on the interface returns a hidden implementation
        static Ledger create() { return entry -> System.out.println("  ledger <- " + entry); }
    }

    static String describe(IbanResult r) {
        return switch (r) {                               // no default: the compiler checks every case is here
            case Ok ok -> "ok: " + ok.iban();
            case TooShort t -> "too short (" + t.length() + " chars)";
            case BadCountry b -> "bad country code '" + b.prefix() + "'";
        };
    }

    public static void main(String[] args) {
        for (String raw : List.of("DE89 3704 0044 0532 0130 00", "DE89 3704", "12345678901234567890")) {
            System.out.println("parse(\"" + raw + "\") -> " + describe(Iban.parse(raw)));
        }
        System.out.println("Fee.of(290) == Fee.of(290)? " + (Fee.of(290) == Fee.of(290)));
        System.out.println("Fee.of(150) == Fee.of(150)? " + (Fee.of(150) == Fee.of(150)));
        Ledger.create().post("fee 29.00 EUR");
    }
}
