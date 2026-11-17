package workbench.functional.l02.demo;

import java.util.List;
import java.util.function.IntConsumer;
import java.util.function.Predicate;

/**
 * Java twin of FourWays.kt. Java has no function types, so each value is an instance of a functional
 * interface, here Predicate<Integer>. Java has no receiver types either: Kotlin's Int.() -> Boolean has no twin.
 */
public class FourWaysJava {

    // 1. A lambda.
    static final Predicate<Integer> TOO_SLOW_LAMBDA = minutes -> minutes > 60;

    // 2. An anonymous class: the closest Java has to an anonymous function. `return` leaves test().
    static final Predicate<Integer> TOO_SLOW_ANON = new Predicate<>() {
        @Override
        public boolean test(Integer minutes) {
            if (minutes < 0) return true;          // a negative time is a typo, so flag it too
            return minutes > 60;
        }
    };

    // 3. A method reference to an ordinary method.
    static boolean isTooSlow(Integer minutes) { return minutes > 60; }
    static final Predicate<Integer> TOO_SLOW_REF = FourWaysJava::isTooSlow;

    // 4. A class that implements the interface.
    static final class TooSlow implements Predicate<Integer> {
        private final int maxMinutes;
        TooSlow(int maxMinutes) { this.maxMinutes = maxMinutes; }
        @Override public boolean test(Integer minutes) { return minutes > maxMinutes; }
    }

    // An optional callback: Java can't say "nullable" in the type, so null is just allowed by convention.
    static boolean check(int minutes, Predicate<Integer> rule, IntConsumer onHit) {
        boolean hit = rule.test(minutes);
        if (hit && onHit != null) onHit.accept(minutes);
        return hit;
    }

    public static void main(String[] args) {
        List<Predicate<Integer>> rules = List.of(TOO_SLOW_LAMBDA, TOO_SLOW_ANON, TOO_SLOW_REF, new TooSlow(60));
        for (int minutes : new int[] {45, 90, -5}) {
            System.out.println(minutes + " -> " + rules.stream().map(rule -> rule.test(minutes)).toList());
        }
        check(90, TOO_SLOW_REF, m -> System.out.println("callback: " + m + " minutes is too slow"));
        System.out.println("no callback given: " + check(90, TOO_SLOW_REF, null));
    }
}
