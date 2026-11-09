package workbench.functional.l07;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/** Java equivalent: the JDK has no Either. A small sealed result and a list of errors do both jobs by hand. */
public class EitherDemoJava {
    sealed interface FormError {}
    record InvalidAmount(long amountMinor) implements FormError {}
    record UnsupportedCurrency(String code) implements FormError {}

    record Amount(long minor, String currency) {}

    sealed interface Validated<A> {}
    record Valid<A>(A value) implements Validated<A> {}
    record Invalid<A>(List<FormError> errors) implements Validated<A> {}

    static final Set<String> CURRENCIES = Set.of("EUR", "USD", "GBP");

    /** Stops at the first failure: the second check never runs. */
    static Validated<Amount> failFast(long a, String c) {
        if (a <= 0) return new Invalid<>(List.of(new InvalidAmount(a)));
        if (!CURRENCIES.contains(c)) return new Invalid<>(List.of(new UnsupportedCurrency(c)));
        return new Valid<>(new Amount(a, c));
    }

    /** Runs every check and collects every failure. */
    static Validated<Amount> accumulate(long a, String c) {
        List<FormError> errors = new ArrayList<>();
        if (a <= 0) errors.add(new InvalidAmount(a));
        if (!CURRENCIES.contains(c)) errors.add(new UnsupportedCurrency(c));
        return errors.isEmpty() ? new Valid<>(new Amount(a, c)) : new Invalid<>(List.copyOf(errors));
    }

    public static void main(String[] args) {
        System.out.println("fail fast:  " + failFast(-5, "XYZ"));
        System.out.println("accumulate: " + accumulate(-5, "XYZ"));
        System.out.println("all good:   " + accumulate(4_250, "EUR"));
    }
}
