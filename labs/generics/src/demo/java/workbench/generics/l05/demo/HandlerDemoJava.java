package workbench.generics.l05.demo;

import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Java twin of HandlerDemo.kt. Java's Consumer and Function are ordinary invariant interfaces,
 * so the flexibility has to be spelled at the use site: ? super for the input, ? extends for the output.
 */
public class HandlerDemoJava {
    public static void main(String[] args) {
        Consumer<Fruit> weighAny = f -> System.out.println("scale: " + f + ", " + f.getGrams() + " g");
        Function<Fruit, String> label = f -> "price card for " + f;

        Consumer<? super Apple> weighApple = weighAny;
        Function<? super Apple, ? extends Object> appleLabel = label;
        weighApple.accept(new Apple("Gala", 180));
        System.out.println(appleLabel.apply(new Apple("Fuji", 150)));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // Consumer<Apple> strict = weighAny;
        // Function<Apple, Object> strictFn = label;
    }
}
