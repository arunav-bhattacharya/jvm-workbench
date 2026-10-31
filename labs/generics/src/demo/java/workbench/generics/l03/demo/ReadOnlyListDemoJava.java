package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ReadOnlyListDemo.kt. Java has no read-only List type, so it writes the read-only view as ? extends. */
public class ReadOnlyListDemoJava {
    public static void main(String[] args) {
        List<String> ms = new ArrayList<>(List.of("a"));
        Integer[] ints = { 1, 2 };

        List<? extends Object> view = ms;          // compiles: a read-only view, spelled at the use site
        System.out.println("as List<? extends Object>: " + view + ", first is a " + view.get(0).getClass().getSimpleName());

        // List<Object> ma = ms;                   // 1
        // Object[] anys = ints;                   // 2
        // view.add(42);                           // 3
        // List<String> back = view;               // 4
        System.out.println("ints: " + ints[0] + ", " + ints[1]);
    }
}
