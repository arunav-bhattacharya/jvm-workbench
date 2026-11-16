package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java arrays are covariant, so the JVM must check every store. Java generics are invariant instead. */
public class ArrayStoreDemo {

    interface Fruit { String name(); }
    record Apple(String name) implements Fruit {}
    record Lemon(String name) implements Fruit {}

    public static void main(String[] args) {
        Apple[] crate = { new Apple("Gala"), new Apple("Fuji") };
        Fruit[] anyFruit = crate;                  // compiles: an Apple[] is a Fruit[]
        try {
            anyFruit[0] = new Lemon("Eureka");     // compiles too: a Lemon is a Fruit
            System.out.println("stored a lemon");
        } catch (ArrayStoreException e) {
            System.out.println("ArrayStoreException: " + e.getMessage());
        }

        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala")));
        // Step 2: uncomment the next line and run. javac refuses it.
        // List<Fruit> fruitList = apples;
        System.out.println("crate[0] is still " + crate[0].name());
    }
}
