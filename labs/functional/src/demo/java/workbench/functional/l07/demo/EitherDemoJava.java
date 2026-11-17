package workbench.functional.l07.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/** Java equivalent: the JDK has no Either. A small sealed result and a list of errors do both jobs by hand. */
public class EitherDemoJava {
    sealed interface FormError {}
    record InvalidAmount(int amount) implements FormError {}
    record UnsupportedUnit(String unit) implements FormError {}

    record Amount(int amount, String unit) {}

    sealed interface Validated<A> {}
    record Valid<A>(A value) implements Validated<A> {}
    record Invalid<A>(List<FormError> errors) implements Validated<A> {}

    static final Set<String> UNITS = Set.of("g", "ml", "pcs");

    /** Stops at the first failure: the second check never runs. */
    static Validated<Amount> failFast(int a, String u) {
        if (a <= 0) return new Invalid<>(List.of(new InvalidAmount(a)));
        if (!UNITS.contains(u)) return new Invalid<>(List.of(new UnsupportedUnit(u)));
        return new Valid<>(new Amount(a, u));
    }

    /** Runs every check and collects every failure. */
    static Validated<Amount> accumulate(int a, String u) {
        List<FormError> errors = new ArrayList<>();
        if (a <= 0) errors.add(new InvalidAmount(a));
        if (!UNITS.contains(u)) errors.add(new UnsupportedUnit(u));
        return errors.isEmpty() ? new Valid<>(new Amount(a, u)) : new Invalid<>(List.copyOf(errors));
    }

    public static void main(String[] args) {
        System.out.println("fail fast:  " + failFast(-5, "oz"));
        System.out.println("accumulate: " + accumulate(-5, "oz"));
        System.out.println("all good:   " + accumulate(250, "g"));
    }
}
