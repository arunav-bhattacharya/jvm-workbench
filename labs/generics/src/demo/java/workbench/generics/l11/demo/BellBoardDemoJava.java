package workbench.generics.l11.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** Java twin of BellBoardDemo.kt. The listener parameter says ? super E: Consumer Super. */
public class BellBoardDemoJava {

    static final class Bells {
        private final List<Consumer<Fruit>> adapters = new ArrayList<>();

        <E extends Fruit> void listen(Class<E> type, Consumer<? super E> listener) {
            adapters.add(item -> {                                     // takes any fruit...
                if (type.isInstance(item)) listener.accept(type.cast(item));   // ...passes on only an E
            });
        }

        void ring(Fruit item) { adapters.forEach(a -> a.accept(item)); }
    }

    public static void main(String[] args) {
        Bells bells = new Bells();
        Consumer<Fruit> stockCount = f -> System.out.println("stock: one more " + f.getName());
        bells.listen(Apple.class, a -> System.out.println("sign for " + a.getName() + ", " + a.getGrams() + " g"));
        bells.listen(Apple.class, stockCount);
        bells.listen(Lemon.class, l -> System.out.println("lemon tray: " + l.getName()));

        bells.ring(new Apple("Gala", 180));
        bells.ring(new Lemon("Eureka", 120));
    }
}
