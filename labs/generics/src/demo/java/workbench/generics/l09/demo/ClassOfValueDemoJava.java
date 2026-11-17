package workbench.generics.l09.demo;

import java.util.List;

/** Java twin of ClassOfValueDemo.kt. getClass() is declared to return Class<? extends |X|>. */
public class ClassOfValueDemoJava {
    public static void main(String[] args) {
        List<Fruit> delivery = List.of(new Apple("Gala", 180), new Lemon("Eureka", 120));
        for (Fruit fruit : delivery) {
            Class<? extends Fruit> c = fruit.getClass();           // the class of SOME Fruit
            System.out.println(fruit.getName() + ": " + c.getSimpleName() + ", is an apple: " + (c == Apple.class));
        }

        Class<Apple> exact = Apple.class;                          // a class literal is exact
        String note = null;                                        // a value that turns out to be null
        try {
            System.out.println(note.getClass());
        } catch (NullPointerException e) {
            System.out.println("exact = " + exact.getSimpleName() + ", getClass() on null: NullPointerException");
        }

        // Wrong move. Uncomment, predict the error, then run.
        // Class<Fruit> strict = delivery.get(0).getClass();
    }
}
