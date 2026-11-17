package workbench.functional.l03.demo;

import java.util.List;
import java.util.Map;
import java.util.function.Function;

/** Java twin of GramsFor.kt. Partial application and currying with java.util.function.Function. */
public class GramsForJava {

    // Roughly what one litre weighs, in grams. The jug measures millilitres; the scale wants grams.
    static final Map<String, Integer> WEIGHT_PER_LITRE = Map.of("flour", 530, "milk", 1_030, "honey", 1_420);

    // Both arguments at once.
    static int grams(String ingredient, int ml) {
        return ml * WEIGHT_PER_LITRE.get(ingredient) / 1_000;
    }

    // Partial application: fix the ingredient now, get back a function of the volume.
    static Function<Integer, Integer> gramsFor(String ingredient) {
        int perLitre = WEIGHT_PER_LITRE.get(ingredient);       // looked up once, right here
        return ml -> ml * perLitre / 1_000;
    }

    // Currying by hand: the type says it all.
    static final Function<String, Function<Integer, Integer>> CURRIED_GRAMS =
            ingredient -> ml -> grams(ingredient, ml);

    public static void main(String[] args) {
        Function<Integer, Integer> honey = gramsFor("honey");
        System.out.println("gramsFor(\"honey\").apply(250)             = " + honey.apply(250));
        System.out.println("CURRIED_GRAMS.apply(\"flour\").apply(500)  = " + CURRIED_GRAMS.apply("flour").apply(500));

        // A lambda that fixes one argument. (Java has no named arguments.)
        Function<Integer, Integer> milkGrams = ml -> grams("milk", ml);
        System.out.println("lambda that fixes milk                   = " + milkGrams.apply(250));

        List<Integer> jugs = List.of(100, 250, 1_000);
        System.out.println("jugs.stream().map(honey)                 = " + jugs.stream().map(honey).toList());
    }
}
