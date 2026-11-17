package workbench.generics.l05.demo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Java twin of PecsDemo.kt. Producer extends, consumer super: the JDK's own copy has both. */
public class PecsDemoJava {

    // the same shape as java.util.Collections.copy(List<? super T> dest, List<? extends T> src)
    static <T> void copyInto(List<? extends T> from, List<? super T> to) {
        for (T x : from) to.add(x);
    }

    public static void main(String[] args) {
        List<Apple> apples = List.of(new Apple("Gala", 180), new Apple("Fuji", 150));
        List<Fruit> shelf = new ArrayList<>(List.of(new Lemon("Eureka", 120)));
        List<Object> anything = new ArrayList<>(List.of("a paper bag"));

        copyInto(apples, shelf);          // T = Apple, or Fruit: both work
        copyInto(apples, anything);
        System.out.println("shelf = " + shelf + ", anything = " + anything);

        List<Fruit> slots = new ArrayList<>(Collections.nCopies(2, new Lemon("Eureka", 95)));
        Collections.copy(slots, apples);  // the JDK version overwrites the slots in place
        System.out.println("slots = " + slots);

        // Wrong move. Uncomment, predict the error, then run.
        // copyInto(shelf, new ArrayList<Apple>());
    }
}
