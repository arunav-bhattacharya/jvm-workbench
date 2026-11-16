package workbench.generics.l01.demo;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Java twin of InferenceDemo.kt. Make javac tell you what `var` inferred: assign the value to an int,
 * which is wrong on purpose. Uncomment ONE probe at a time, run, read the message, comment it out again.
 */
public class InferenceDemoJava {
    public static void main(String[] args) {
        var weights = List.of(180, 150, 210);
        var mixed = List.of(180, 2.5);
        var tags = Arrays.asList("ripe", null);
        var prices = Map.of("apple", 40, "mango", 250L);
        var varieties = new ArrayList<String>();          // Java has no buildList: say the type up front
        varieties.add("Gala");
        varieties.add("Fuji");
        var none = Collections.emptyList();               // no error in Java: what did it pick?

        // int probe1 = weights;
        // int probe2 = mixed;
        // int probe3 = tags;
        // int probe4 = prices;
        // int probe5 = varieties;
        // int probe6 = none;

        System.out.println("compiled: " + (weights.size() + mixed.size() + tags.size() + prices.size() + varieties.size() + none.size()) + " values");
    }
}
