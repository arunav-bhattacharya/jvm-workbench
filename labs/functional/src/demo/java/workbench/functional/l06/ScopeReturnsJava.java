package workbench.functional.l06;

import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Java has no scope functions and no lambdas with a receiver. This is what each one stands in for,
 * plus the two shapes written as static methods.
 */
public class ScopeReturnsJava {
    record Charge(String id, long amountMinor, String currency) {}

    static class ChargeRequest {
        long amountMinor;
        String currency = "";
        @Override public String toString() { return "ChargeRequest(" + amountMinor + " " + currency + ")"; }
    }

    // let: hand the value to a function, return what it returns
    static <T, R> R let(T value, Function<T, R> block) { return block.apply(value); }

    // apply/also: hand the value to a block, return the value itself
    static <T> T apply(T value, Consumer<T> block) { block.accept(value); return value; }

    public static void main(String[] args) {
        Charge charge = new Charge("ch_1", 1_999, "EUR");

        // let, run and with all compute something from the object
        System.out.println("computed -> " + charge.amountMinor() * 2);
        // also and apply keep the object, whatever the block did
        System.out.println("kept     -> " + charge);

        System.out.println("let      -> " + let(charge, c -> c.amountMinor() * 2));
        // no receiver: the block must name its parameter and write r. on every line
        System.out.println("apply    -> " + apply(new ChargeRequest(), r -> { r.amountMinor = 1_999; r.currency = "EUR"; }));
    }
}
