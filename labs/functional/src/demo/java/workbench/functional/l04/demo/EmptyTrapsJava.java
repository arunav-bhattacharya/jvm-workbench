package workbench.functional.l04.demo;

import java.util.List;
import java.util.function.Supplier;

/** Java twin of EmptyTraps.kt. Java's answer to "no elements" is mostly Optional. */
public class EmptyTrapsJava {

    // Runs one expression and prints its value, or the exception it threw.
    static void attempt(String label, Supplier<Object> block) {
        String result;
        try {
            result = String.valueOf(block.get());
        } catch (RuntimeException e) {
            result = "throws " + e;
        }
        System.out.printf("%-40s %s%n", label, result);
    }

    public static void main(String[] args) {
        List<Integer> none = List.of();                    // a day when nothing was baked
        attempt("reduce(0, Integer::sum)", () -> none.stream().reduce(0, Integer::sum));
        attempt("mapToInt(x -> x).sum()", () -> none.stream().mapToInt(x -> x).sum());
        attempt("reduce(Integer::sum)", () -> none.stream().reduce(Integer::sum));
        attempt("findFirst()", () -> none.stream().findFirst());
        attempt("findFirst().orElseThrow()", () -> none.stream().findFirst().orElseThrow());
        attempt("get(0)", () -> none.get(0));
        attempt("max(Integer::compare)", () -> none.stream().max(Integer::compare));
    }
}
