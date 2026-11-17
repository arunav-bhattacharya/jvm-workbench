package workbench.generics.l06.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of ChooseDemo.kt. Java has only use-site variance, so every class is like Crate:
 * invariant, with ? extends or ? super written by each method that only reads or only writes.
 */
public class ChooseDemoJava {

    static final class Crate<T> {
        private final List<T> items = new ArrayList<>();
        void put(T item) { items.add(item); }
        T top() { return items.get(items.size() - 1); }
    }

    // only takes out: ? extends
    static String topName(Crate<? extends Fruit> crate) { return crate.top().getName(); }

    // only puts apples in: ? super
    static void putApple(Crate<? super Apple> crate, String name, int grams) {
        crate.put(new Apple(name, grams));
    }

    public static void main(String[] args) {
        Crate<Apple> apples = new Crate<>();
        Crate<Fruit> mixed = new Crate<>();
        mixed.put(new Lemon("Eureka", 120));

        putApple(apples, "Gala", 180);
        putApple(mixed, "Fuji", 150);
        System.out.println(topName(apples) + " " + topName(mixed));

        // Wrong move: the class is invariant, so the plain type still doesn't fit.
        // Crate<Fruit> strict = apples;
    }
}
