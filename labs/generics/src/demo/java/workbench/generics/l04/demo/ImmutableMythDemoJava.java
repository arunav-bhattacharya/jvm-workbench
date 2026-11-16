package workbench.generics.l04.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ImmutableMythDemo.kt. A ? extends view stops adds, not changes. Fruit and Apple come from ProducerDemo.kt. */
public class ImmutableMythDemoJava {
    public static void main(String[] args) {
        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala", 180), new Apple("Fuji", 150)));
        List<? extends Fruit> view = apples;            // read-only for the TYPE, not for the state

        Fruit taken = view.remove(0);                   // compiles: remove hands a value out
        System.out.println("took " + taken.getName() + ", " + view.size() + " left");
        view.clear();                                   // compiles: no T involved
        System.out.println("after clear: " + view.size() + " left, and apples has " + apples.size());

        // view.add(new Apple("Pink Lady", 170));       // uncomment: which rule stops this?
    }
}
