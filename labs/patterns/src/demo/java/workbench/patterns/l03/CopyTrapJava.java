package workbench.patterns.l03;

import java.util.ArrayList;
import java.util.List;

/** The Java twin of CopyTrap.kt: record copies are shallow, and a factory can't hide a record's constructor. */
public class CopyTrapJava {
    record Cart(String id, List<String> skus) {
        Cart withId(String newId) { return new Cart(newId, skus); }      // a hand-written wither: shares the list
    }

    record Email(String value) {
        // a record's canonical constructor is never more private than the record itself,
        // so this factory can always be bypassed with new Email(...)
        static Email of(String raw) {
            if (!raw.contains("@")) throw new IllegalArgumentException("not an email: " + raw);
            return new Email(raw);
        }
    }

    record Amount(long minor) {
        Amount {                                                      // compact constructor: every path runs it
            if (minor < 0) throw new IllegalArgumentException("negative amount: " + minor);
        }
        Amount withMinor(long m) { return new Amount(m); }
    }

    public static void main(String[] args) {
        // trap 1: the wither copies the reference to the list, not the list
        Cart c1 = new Cart("c1", new ArrayList<>(List.of("sku-1")));
        Cart c2 = c1.withId("c2");
        c2.skus().add("sku-2");
        System.out.println("c1.skus after changing c2: " + c1.skus());

        // trap 2: the factory validates, the canonical constructor doesn't
        Email broken = new Email("not-an-email");
        System.out.println("new skipped the factory: " + broken);

        // the compact constructor DOES run on withers
        try {
            new Amount(5).withMinor(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("new Amount(5).withMinor(-1): " + e.getMessage());
        }
    }
}
