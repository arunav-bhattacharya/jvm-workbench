package workbench.generics.l07.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of StarListDemo.kt. List<?> is Java's "list of some type I don't know". */
public class StarListDemoJava {

    static void logAll(List<?> items) {
        for (Object item : items) System.out.println("  " + item);   // each item is an Object
    }

    static int reset(List<?> buffer) {
        int n = buffer.size();
        buffer.clear();                                                // takes no element: allowed
        return n;
    }

    public static void main(String[] args) {
        List<String> ids = new ArrayList<>(List.of("pay_1", "pay_2"));
        List<Integer> cents = new ArrayList<>(List.of(1_200, 350, 99));
        logAll(ids);
        logAll(cents);

        List<?> star = ids;
        Object first = star.get(0);                                    // reading gives Object
        System.out.println("first = " + first + ", removed " + reset(ids) + " ids and " + reset(cents) + " amounts");

        star.add(null);                                                // Java allows null here; Kotlin does not
        System.out.println("after add(null): " + ids);

        // Wrong moves. Uncomment one at a time, predict the error, then run.
        // star.add("pay_3");                                         // 1
        // String id = star.get(0);                                   // 3
    }
}
