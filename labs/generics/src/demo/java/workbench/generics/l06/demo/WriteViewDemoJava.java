package workbench.generics.l06.demo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Java twin of WriteViewDemo.kt. ? super at the use site is Kotlin's in-projection. */
public class WriteViewDemoJava {

    static void restock(List<? super Apple> crate, int count) {
        for (int i = 0; i < count; i++) crate.add(new Apple("Gala", 180));   // putting an Apple in: fine
        Object first = crate.isEmpty() ? null : crate.get(0);              // reading compiles, as Object
        System.out.println("  first is " + first);
        // Apple firstApple = crate.get(0);                                // wrong move 1: ? super can't promise an Apple
    }

    public static void main(String[] args) {
        List<Apple> apples = new ArrayList<>(List.of(new Apple("Fuji", 150)));
        List<Fruit> fruit = new ArrayList<>(List.of(new Lemon("Eureka", 120)));
        List<Object> anything = new ArrayList<>(List.of("a paper bag"));
        restock(apples, 1);
        restock(fruit, 2);
        restock(anything, 2);
        System.out.println("apples = " + apples + ", fruit = " + fruit + ", anything = " + anything);

        Collections.fill(fruit, new Apple("Fuji", 150));                    // fill(List<? super T> list, T obj)
        System.out.println("after Collections.fill: " + fruit);

        // Wrong move 2: a crate of lemons can't take an apple.
        // restock(new ArrayList<Lemon>(List.of(new Lemon("Eureka", 95))), 1);
    }
}
