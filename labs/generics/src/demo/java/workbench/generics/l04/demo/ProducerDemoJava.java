package workbench.generics.l04.demo;

import java.util.Iterator;
import java.util.List;

/**
 * Java twin of ProducerDemo.kt. Java has no `out` on a declaration, so Dispenser<T> stays invariant
 * and every method that wants "a dispenser of some kind of Fruit" says so at the use site: ? extends.
 * Fruit and Apple are the Kotlin types from ProducerDemo.kt.
 */
public class ProducerDemoJava {

    interface Dispenser<T> {
        T next();                                  // null when it is empty
    }

    static <T> Dispenser<T> listDispenser(List<T> items) {
        Iterator<T> it = items.iterator();
        return () -> it.hasNext() ? it.next() : null;
    }

    // ? extends Fruit: "a Dispenser of Fruit or of some subtype". Without it, a Dispenser<Apple> would not fit.
    static int totalGrams(Dispenser<? extends Fruit> dispenser) {
        int sum = 0;
        for (Fruit f = dispenser.next(); f != null; f = dispenser.next()) sum += f.getGrams();
        return sum;
    }

    public static void main(String[] args) {
        Dispenser<Apple> apples = listDispenser(List.of(new Apple("Gala", 180), new Apple("Fuji", 150)));
        System.out.println("apple total: " + totalGrams(apples) + " g");

        Dispenser<? extends Object> anything = listDispenser(List.of("a paper bag"));
        System.out.println("first from anything: " + anything.next());

        // Wrong move. Uncomment, predict the error, then run.
        // Dispenser<Fruit> plain = apples;
    }
}
