package workbench.functional.l01.demo;

import java.util.List;

/** Java twin of ReplaceTheCall.kt: swapping a call for its value is safe only when the call is pure. */
public class ReplaceTheCallJava {

    // Pure: the result depends only on the argument, and calling it changes nothing.
    static long fee(long amountCents) {
        return amountCents * 15 / 1000;
    }

    // Impure: charging a card is the whole point of the call. This fake provider counts the calls.
    static int calls = 0;

    static String charge(String cardToken, long amountCents) {
        calls++;
        return "ch_" + calls;
    }

    public static void main(String[] args) {
        // 1. With a pure function, a call and its value are interchangeable.
        long f = fee(20_000);
        System.out.println("fee(20000) + fee(20000)    = " + (fee(20_000) + fee(20_000)));
        System.out.println("long f = fee(20000); f + f = " + (f + f));

        // 2. The same "harmless" refactoring on an impure call changes what the program does.
        String c = charge("tok_visa", 20_000);
        System.out.println("String c = charge(..); List.of(c, c)   -> " + List.of(c, c) + ", provider calls: " + calls);

        calls = 0;
        List<String> both = List.of(charge("tok_visa", 20_000), charge("tok_visa", 20_000));
        System.out.println("List.of(charge(..), charge(..))        -> " + both + ", provider calls: " + calls);
    }
}
