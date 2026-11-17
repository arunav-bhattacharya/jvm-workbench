package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of InvarianceDemo.kt. What would go wrong if a List<Apple> were a List<Fruit>? */
public class InvarianceDemoJava {

    interface Fruit { String name(); }
    record Apple(String name) implements Fruit {}
    record Lemon(String name) implements Fruit {}

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala")));

        // Step 1: uncomment this line and run. javac refuses it.
        // List<Fruit> view = apples;

        // Step 2: force it through a wildcard cast. This compiles, with an unchecked warning.
        List<Fruit> anyFruit = (List<Fruit>) (List<?>) apples;
        anyFruit.add(new Lemon("Eureka"));         // fine for a list of any fruit
        System.out.println("the apple crate holds " + apples.size() + " items, and nothing failed yet");

        try {
            Apple second = apples.get(1);          // javac inserted a cast to Apple here
            System.out.println("second apple: " + second.name());
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
    }
}
