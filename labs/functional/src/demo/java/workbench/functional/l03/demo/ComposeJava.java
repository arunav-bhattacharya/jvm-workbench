package workbench.functional.l03.demo;

import java.util.List;
import java.util.function.Function;

/** Java twin of Compose.kt. java.util.function.Function has andThen and compose built in, as default methods. */
public class ComposeJava {

    static final Function<Integer, Integer> FOR_SIX_GUESTS = g -> g * 6 / 4;       // the recipe serves four
    static final Function<Integer, Integer> TEN_PERCENT_LESS = g -> g * 90 / 100;  // less sugar, rounded down
    static final Function<Integer, Integer> AT_MOST_THE_BAG = g -> Math.min(g, 250); // only 250 g left in the bag

    public static void main(String[] args) {
        Function<Integer, Integer> sugar = FOR_SIX_GUESTS.andThen(TEN_PERCENT_LESS).andThen(AT_MOST_THE_BAG);
        Function<Integer, Integer> capFirst = AT_MOST_THE_BAG.andThen(FOR_SIX_GUESTS).andThen(TEN_PERCENT_LESS);
        for (int grams : new int[] {100, 200}) {
            System.out.println("recipe says " + grams + " g -> " + sugar.apply(grams) + " g   (cap first: " + capFirst.apply(grams) + " g)");
        }

        // Built from a list, the way a saved set of adjustments would build it.
        List<Function<Integer, Integer>> steps = List.of(FOR_SIX_GUESTS, TEN_PERCENT_LESS, AT_MOST_THE_BAG);
        Function<Integer, Integer> fromList = steps.stream()
                .reduce(Function.identity(), (acc, step) -> acc.andThen(step));
        System.out.println("fromList(200) = " + fromList.apply(200));
    }
}
