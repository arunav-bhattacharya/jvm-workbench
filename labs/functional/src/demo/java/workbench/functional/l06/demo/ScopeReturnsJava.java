package workbench.functional.l06.demo;

import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Java has no scope functions and no lambdas with a receiver. This is what each one stands in for,
 * plus the two shapes written as static methods.
 */
public class ScopeReturnsJava {
    record Recipe(String name, int servings, int grams) {}

    static class TraySetup {
        boolean paper;
        int cookies;
        @Override public String toString() { return "TraySetup(paper=" + paper + ", cookies=" + cookies + ")"; }
    }

    // let: hand the value to a function, return what it returns
    static <T, R> R let(T value, Function<T, R> block) { return block.apply(value); }

    // apply/also: hand the value to a block, return the value itself
    static <T> T apply(T value, Consumer<T> block) { block.accept(value); return value; }

    public static void main(String[] args) {
        Recipe recipe = new Recipe("pancakes", 4, 200);

        // let, run and with all compute something from the object
        System.out.println("computed -> " + recipe.servings() * 2);
        // also and apply keep the object, whatever the block did
        System.out.println("kept     -> " + recipe);

        System.out.println("let      -> " + let(recipe, r -> r.servings() * 2));
        // no receiver: the block must name its parameter and write t. on every line
        System.out.println("apply    -> " + apply(new TraySetup(), t -> { t.paper = true; t.cookies = 12; }));
    }
}
