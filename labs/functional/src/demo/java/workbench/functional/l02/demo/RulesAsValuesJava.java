package workbench.functional.l02.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;

/** Java twin of RulesAsValues.kt. A rule is a Function<Payment, Rejection> that returns null when the payment passes. */
public class RulesAsValuesJava {

    record Payment(String id, long amountCents, String currency, String country) {}
    record Rejection(String rule, String paymentId) {}

    // Each rule is a value: a lambda stored in a field, ready to go into a list.
    static final Function<Payment, Rejection> MAX_AMOUNT =
            p -> p.amountCents() > 500_000 ? new Rejection("amount-limit", p.id()) : null;
    static final Function<Payment, Rejection> SERVED_COUNTRY =
            p -> Set.of("NL", "BE", "DE").contains(p.country()) ? null : new Rejection("country-not-served", p.id());
    static final Function<Payment, Rejection> EURO_ONLY =
            p -> p.currency().equals("EUR") ? null : new Rejection("currency-not-supported", p.id());
    static final Function<Payment, Rejection> NO_MICRO_PAYMENTS =
            p -> p.amountCents() < 100 ? new Rejection("micro-payment", p.id()) : null;

    // Different merchants get different lists. Adding a rule for one merchant changes nothing above.
    static final List<Function<Payment, Rejection>> STANDARD = List.of(MAX_AMOUNT, SERVED_COUNTRY, EURO_ONLY);
    static final List<Function<Payment, Rejection>> MARKETPLACE = plus(STANDARD, NO_MICRO_PAYMENTS);

    static <T> List<T> plus(List<T> list, T extra) {
        List<T> copy = new ArrayList<>(list);
        copy.add(extra);
        return List.copyOf(copy);
    }

    // Run the rules in order and stop at the first rejection. A rule is called with apply.
    static Rejection firstRejection(Payment p, List<Function<Payment, Rejection>> rules) {
        for (Function<Payment, Rejection> rule : rules) {
            Rejection r = rule.apply(p);
            if (r != null) return r;
        }
        return null;
    }

    static String name(Rejection r) {
        return r == null ? "ok" : r.rule();
    }

    public static void main(String[] args) {
        List<Payment> payments = List.of(
                new Payment("pay_1", 12_000, "EUR", "NL"),
                new Payment("pay_2", 900_000, "EUR", "DE"),
                new Payment("pay_3", 50, "EUR", "BE"),
                new Payment("pay_4", 4_000, "USD", "US"));
        for (Payment p : payments) {
            System.out.println(p.id() + ": standard=" + name(firstRejection(p, STANDARD))
                    + ", marketplace=" + name(firstRejection(p, MARKETPLACE)));
        }
    }
}
