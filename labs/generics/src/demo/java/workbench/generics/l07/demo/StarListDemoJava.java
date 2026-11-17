package workbench.generics.l07.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of StarListDemo.kt. List<?> is Java's "list of some type I don't know". */
public class StarListDemoJava {

    static void printAll(List<?> items) {
        for (Object item : items) System.out.println("  " + item);   // each item is an Object
    }

    static int empty(List<?> crate) {
        int n = crate.size();
        crate.clear();                                                 // takes no element: allowed
        return n;
    }

    public static void main(String[] args) {
        List<String> varieties = new ArrayList<>(List.of("Gala", "Fuji"));
        List<Integer> weights = new ArrayList<>(List.of(180, 150, 120));
        printAll(varieties);
        printAll(weights);

        List<?> unlabeled = varieties;
        Object first = unlabeled.get(0);                               // reading gives Object
        System.out.println("first = " + first + ", emptied " + empty(varieties) + " names and " + empty(weights) + " weights");

        unlabeled.add(null);                                           // Java allows null here; Kotlin does not
        System.out.println("after add(null): " + varieties);

        // Wrong moves. Uncomment one at a time, predict the error, then run.
        // unlabeled.add("Eureka");                                   // 1
        // String name = unlabeled.get(0);                            // 3
    }
}
