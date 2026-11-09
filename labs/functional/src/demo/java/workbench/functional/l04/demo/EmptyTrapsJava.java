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
        List<Long> none = List.of();                       // a quiet day: no payments at all
        attempt("reduce(0L, Long::sum)", () -> none.stream().reduce(0L, Long::sum));
        attempt("mapToLong(x -> x).sum()", () -> none.stream().mapToLong(x -> x).sum());
        attempt("reduce(Long::sum)", () -> none.stream().reduce(Long::sum));
        attempt("findFirst()", () -> none.stream().findFirst());
        attempt("findFirst().orElseThrow()", () -> none.stream().findFirst().orElseThrow());
        attempt("get(0)", () -> none.get(0));
        attempt("max(Long::compare)", () -> none.stream().max(Long::compare));
    }
}
