package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ReadOnlyListDemo.kt. Java has no read-only List type, so it writes the read-only view as ? extends. */
public class ReadOnlyListDemoJava {

    interface Fruit { String name(); }
    record Apple(String name) implements Fruit {}
    record Lemon(String name) implements Fruit {}

    public static void main(String[] args) {
        List<Apple> crate = new ArrayList<>(List.of(new Apple("Gala")));
        Integer[] weights = { 180, 150 };

        List<? extends Fruit> display = crate;      // compiles: a read-only view, spelled at the use site
        System.out.println("as List<? extends Fruit>: " + display + ", first is a " + display.get(0).getClass().getSimpleName());

        // List<Fruit> anyCrate = crate;            // 1
        // Object[] anys = weights;                 // 2
        // display.add(new Lemon("Eureka"));        // 3
        // List<Apple> back = display;              // 4
        System.out.println("weights: " + weights[0] + ", " + weights[1]);
    }
}
