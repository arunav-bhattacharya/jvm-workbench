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
        var amounts = List.of(1200, 350, 99);
        var mixed = List.of(1, 2.5);
        var tags = Arrays.asList("card", null);
        var fees = Map.of("EUR", 100, "USD", 250L);
        var keys = new ArrayList<String>();             // Java has no buildList: say the type up front
        keys.add("idem_1");
        keys.add("idem_2");
        var none = Collections.emptyList();             // no error in Java: what did it pick?

        // int probe1 = amounts;
        // int probe2 = mixed;
        // int probe3 = tags;
        // int probe4 = fees;
        // int probe5 = keys;
        // int probe6 = none;

        System.out.println("compiled: " + (amounts.size() + mixed.size() + tags.size() + fees.size() + keys.size() + none.size()) + " values");
    }
}
