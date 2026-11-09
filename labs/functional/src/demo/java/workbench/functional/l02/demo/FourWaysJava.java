package workbench.functional.l02.demo;

import java.util.List;
import java.util.function.LongConsumer;
import java.util.function.Predicate;

/**
 * Java twin of FourWays.kt. Java has no function types, so each value is an instance of a functional
 * interface, here Predicate<Long>. Java has no receiver types either: Kotlin's Long.() -> Boolean has no twin.
 */
public class FourWaysJava {

    // 1. A lambda.
    static final Predicate<Long> OVER_LIMIT_LAMBDA = cents -> cents > 500_000;

    // 2. An anonymous class: the closest Java has to an anonymous function. `return` leaves test().
    static final Predicate<Long> OVER_LIMIT_ANON = new Predicate<>() {
        @Override
        public boolean test(Long cents) {
            if (cents < 0) return true;            // a negative amount is suspicious too
            return cents > 500_000;
        }
    };

    // 3. A method reference to an ordinary method.
    static boolean isOverLimit(Long cents) { return cents > 500_000; }
    static final Predicate<Long> OVER_LIMIT_REF = FourWaysJava::isOverLimit;

    // 4. A class that implements the interface.
    static final class OverLimit implements Predicate<Long> {
        private final long limitCents;
        OverLimit(long limitCents) { this.limitCents = limitCents; }
        @Override public boolean test(Long cents) { return cents > limitCents; }
    }

    // An optional callback: Java can't say "nullable" in the type, so null is just allowed by convention.
    static boolean check(long cents, Predicate<Long> rule, LongConsumer onHit) {
        boolean hit = rule.test(cents);
        if (hit && onHit != null) onHit.accept(cents);
        return hit;
    }

    public static void main(String[] args) {
        List<Predicate<Long>> rules = List.of(OVER_LIMIT_LAMBDA, OVER_LIMIT_ANON, OVER_LIMIT_REF, new OverLimit(500_000));
        for (long cents : new long[] {12_000L, 900_000L, -5L}) {
            System.out.println(cents + " -> " + rules.stream().map(rule -> rule.test(cents)).toList());
        }
        check(900_000, OVER_LIMIT_REF, c -> System.out.println("callback: " + c + " is over the limit"));
        System.out.println("no callback given: " + check(900_000, OVER_LIMIT_REF, null));
    }
}
