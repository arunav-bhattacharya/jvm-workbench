package workbench.patterns.l03;

import java.util.ArrayList;
import java.util.List;

/** The Java twin of CopyTrap.kt: record copies are shallow, and a factory can't hide a record's constructor. */
public class CopyTrapJava {
    record Cart(String id, List<String> items) {
        Cart withId(String newId) { return new Cart(newId, items); }     // a hand-written wither: shares the list
    }

    record Email(String value) {
        // a record's canonical constructor is never more private than the record itself,
        // so this factory can always be bypassed with new Email(...)
        static Email of(String raw) {
            if (!raw.contains("@")) throw new IllegalArgumentException("not an email: " + raw);
            return new Email(raw);
        }
    }

    record Price(long cents) {
        Price {                                                       // compact constructor: every path runs it
            if (cents < 0) throw new IllegalArgumentException("negative price: " + cents);
        }
        Price withCents(long c) { return new Price(c); }
    }

    public static void main(String[] args) {
        // trap 1: the wither copies the reference to the list, not the list
        Cart c1 = new Cart("c1", new ArrayList<>(List.of("bread")));
        Cart c2 = c1.withId("c2");
        c2.items().add("milk");
        System.out.println("c1.items after changing c2: " + c1.items());

        // trap 2: the factory checks, the canonical constructor doesn't
        Email broken = new Email("not-an-email");
        System.out.println("new skipped the factory: " + broken);

        // the compact constructor DOES run on withers
        try {
            new Price(5).withCents(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("new Price(5).withCents(-1): " + e.getMessage());
        }
    }
}
