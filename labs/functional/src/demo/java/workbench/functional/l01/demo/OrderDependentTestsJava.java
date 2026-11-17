package workbench.functional.l01.demo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Java twin of OrderDependentTests.kt: two tests share a static field, so their order decides the result. */
public class OrderDependentTestsJava {

    // A global the shopping helper reads. Whoever cooked last, or a test, can change it at any time.
    static int flourLeft = 700;                  // grams still in the bag

    // Looks harmless. But its answer depends on something that is not in its parameter list.
    static int flourMissing(int neededGrams) {
        return Math.max(neededGrams - flourLeft, 0);
    }

    static String halfBagTest() {
        int missing = flourMissing(1_500);
        return missing == 800 ? "pass" : "FAIL (expected 800, got " + missing + ")";
    }

    // Puts a new bag in the cupboard and never takes it out again.
    static String newBagTest() {
        flourLeft = 1_700;                       // a new 1 kg bag next to the old one
        int missing = flourMissing(1_500);
        return missing == 0 ? "pass" : "FAIL (expected 0, got " + missing + ")";
    }

    public static void main(String[] args) {
        List<Map.Entry<String, Supplier<String>>> tests = new ArrayList<>(List.of(
                Map.entry("halfBag", OrderDependentTestsJava::halfBagTest),
                Map.entry("newBag", OrderDependentTestsJava::newBagTest)));
        if (args.length > 0 && args[0].equals("reverse")) Collections.reverse(tests);
        for (var t : tests) System.out.println(t.getKey() + ": " + t.getValue().get());
    }
}
