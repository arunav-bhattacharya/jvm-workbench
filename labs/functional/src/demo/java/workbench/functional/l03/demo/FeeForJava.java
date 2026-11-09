package workbench.functional.l03.demo;

import java.util.List;
import java.util.Map;
import java.util.function.Function;

/** Java twin of FeeFor.kt. Partial application and currying with java.util.function.Function. */
public class FeeForJava {

    static final Map<String, Long> RATES_BPS = Map.of("NL", 140L, "DE", 150L, "US", 290L);

    // Both arguments at once.
    static long fee(String country, long amountCents) {
        return amountCents * RATES_BPS.get(country) / 10_000;
    }

    // Partial application: fix the country now, get back a function of the amount.
    static Function<Long, Long> feeFor(String country) {
        long bps = RATES_BPS.get(country);                  // looked up once, right here
        return amountCents -> amountCents * bps / 10_000;
    }

    // Currying by hand: the type says it all.
    static final Function<String, Function<Long, Long>> CURRIED_FEE =
            country -> amountCents -> fee(country, amountCents);

    public static void main(String[] args) {
        Function<Long, Long> dutch = feeFor("NL");
        System.out.println("feeFor(\"NL\").apply(100000)            = " + dutch.apply(100_000L));
        System.out.println("CURRIED_FEE.apply(\"DE\").apply(100000) = " + CURRIED_FEE.apply("DE").apply(100_000L));

        // A lambda that fixes one argument. (Java has no named arguments.)
        Function<Long, Long> usFee = amountCents -> fee("US", amountCents);
        System.out.println("lambda that fixes US                  = " + usFee.apply(100_000L));

        List<Long> amounts = List.of(10_000L, 250_000L, 1_000_000L);
        System.out.println("amounts.stream().map(dutch)           = " + amounts.stream().map(dutch).toList());
    }
}
