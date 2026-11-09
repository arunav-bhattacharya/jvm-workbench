package workbench.functional.l03.demo;

import java.util.List;
import java.util.function.Function;

/** Java twin of Compose.kt. java.util.function.Function has andThen and compose built in, as default methods. */
public class ComposeJava {

    static final Function<Long, Long> ADD_SCHEME_FEE = fee -> fee + 25;          // +25 cents
    static final Function<Long, Long> LOYALTY_DISCOUNT = fee -> fee * 90 / 100;  // 10 % off, rounded down
    static final Function<Long, Long> CAP_AT_TEN_EUROS = fee -> Math.min(fee, 1_000);

    public static void main(String[] args) {
        Function<Long, Long> price = ADD_SCHEME_FEE.andThen(LOYALTY_DISCOUNT).andThen(CAP_AT_TEN_EUROS);
        Function<Long, Long> capFirst = CAP_AT_TEN_EUROS.andThen(ADD_SCHEME_FEE).andThen(LOYALTY_DISCOUNT);
        for (long fee : new long[] {500L, 1_200L}) {
            System.out.println("fee " + fee + " -> " + price.apply(fee) + "   (cap first: " + capFirst.apply(fee) + ")");
        }

        // Built from a list, the way merchant configuration would build it.
        List<Function<Long, Long>> steps = List.of(ADD_SCHEME_FEE, LOYALTY_DISCOUNT, CAP_AT_TEN_EUROS);
        Function<Long, Long> fromList = steps.stream()
                .reduce(Function.identity(), (acc, step) -> acc.andThen(step));
        System.out.println("fromList(1200) = " + fromList.apply(1_200L));
    }
}
