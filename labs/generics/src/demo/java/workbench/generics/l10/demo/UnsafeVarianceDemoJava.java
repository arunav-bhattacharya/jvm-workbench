package workbench.generics.l10.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of UnsafeVarianceDemo.kt. Java's contains takes an Object, so it never needed the
 * annotation, and it can't catch a nonsense check. Java's way to break a ? extends view on purpose
 * is an unchecked cast.
 */
public class UnsafeVarianceDemoJava {

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        List<? extends Number> weights = List.of(180, 150);
        System.out.println("contains(150): " + weights.contains(150) + ", contains(2.5): " + weights.contains(2.5));

        System.out.println("contains(\"180\") compiles in Java: " + List.of(180, 150).contains("180"));

        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala", 180)));
        List<? extends Fruit> view = apples;
        ((List<Fruit>) view).add(new Lemon("Eureka", 120));    // the unchecked cast is the Java "unsafe variance"
        try {
            Apple last = apples.get(apples.size() - 1);
            System.out.println(last);
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage().split(" \\(")[0]);
        }
    }
}
