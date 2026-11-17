package workbench.functional.l02.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;

/** Java twin of ChecksAsValues.kt. A check is a Function<Dish, Problem> that returns null when the dish passes. */
public class ChecksAsValuesJava {

    record Dish(String name, int minutes, String diet, String main, boolean nuts) {}
    record Problem(String check, String dish) {}

    // Each check is a value: a lambda stored in a field, ready to go into a list.
    static final Function<Dish, Problem> READY_IN_AN_HOUR =
            d -> d.minutes() > 60 ? new Problem("too-slow", d.name()) : null;
    static final Function<Dish, Problem> AUTUMN_ONLY =
            d -> Set.of("pumpkin", "leek", "apple", "mushroom").contains(d.main()) ? null : new Problem("out-of-season", d.name());
    static final Function<Dish, Problem> MEAT_FREE =
            d -> d.diet().equals("meat") ? new Problem("has-meat", d.name()) : null;

    // Different guests get different lists. Adding a check for one guest changes nothing above.
    static final List<Function<Dish, Problem>> EVERYONE = List.of(READY_IN_AN_HOUR, AUTUMN_ONLY);
    static final List<Function<Dish, Problem>> FOR_SAM = plus(EVERYONE, MEAT_FREE);   // Sam is vegetarian

    static <T> List<T> plus(List<T> list, T extra) {
        List<T> copy = new ArrayList<>(list);
        copy.add(extra);
        return List.copyOf(copy);
    }

    // Run the checks in order and stop at the first problem. A check is called with apply.
    static Problem firstProblem(Dish d, List<Function<Dish, Problem>> checks) {
        for (Function<Dish, Problem> check : checks) {
            Problem p = check.apply(d);
            if (p != null) return p;
        }
        return null;
    }

    static String name(Problem p) {
        return p == null ? "ok" : p.check();
    }

    public static void main(String[] args) {
        List<Dish> dishes = List.of(
                new Dish("pumpkin soup", 40, "vegan", "pumpkin", false),
                new Dish("slow roast", 180, "meat", "beef", false),
                new Dish("leek and bacon tart", 50, "meat", "leek", false),
                new Dish("strawberry cake", 45, "vegetarian", "strawberry", true));
        for (Dish d : dishes) {
            System.out.println(d.name() + ": everyone=" + name(firstProblem(d, EVERYONE))
                    + ", Sam=" + name(firstProblem(d, FOR_SAM)));
        }
    }
}
