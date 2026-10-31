package workbench.patterns.l01;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Currency;
import java.util.List;
import java.util.Collections;

/** Five patterns hiding in the JDK. Predict each line before you run it. */
public class PatternsYouAlreadyUse {
    record Payment(String id, long amountMinor) {}

    public static void main(String[] args) {
        // Singleton: one Runtime per JVM, no public constructor
        System.out.println("1. Runtime is a singleton:      " + (Runtime.getRuntime() == Runtime.getRuntime()));

        // Flyweight: Integer.valueOf caches -128..127, Currency keeps one instance per code
        Integer a = 127, b = 127, c = 128, d = 128;
        System.out.println("2. 127 == 127 (boxed):          " + (a == b));
        System.out.println("3. 128 == 128 (boxed):          " + (c == d));
        System.out.println("4. EUR == EUR (Currency):       " + (Currency.getInstance("EUR") == Currency.getInstance("EUR")));

        // Proxy/decorator view: unmodifiableList reads through to the list it wraps
        List<String> ids = new ArrayList<>(List.of("p-1"));
        List<String> view = Collections.unmodifiableList(ids);
        ids.add("p-2");
        System.out.println("5. view after ids.add(\"p-2\"):   " + view);

        // Strategy: a Comparator is an algorithm you pass in, and a lambda is enough to make one
        List<Payment> payments = new ArrayList<>(List.of(new Payment("p-9", 500), new Payment("p-3", 12_000)));
        payments.sort(Comparator.comparing(Payment::amountMinor).reversed());
        System.out.println("6. sorted by amount, desc:      " + payments.stream().map(Payment::id).toList());
    }
}
