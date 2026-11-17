package workbench.generics.l07.demo;

/**
 * Java twin of StarRulesDemo.kt. Java's ? keeps the declared bound, like Kotlin's *.
 * Fruit, Apple and Lemon are the Kotlin types from StarRulesDemo.kt.
 */
public class StarRulesDemoJava {

    interface Dispenser<T extends Fruit> { T next(); }
    interface Bin<T> { void drop(T item); }
    static final class Box<T> {
        T item;
        Box(T item) { this.item = item; }
    }

    static Fruit peek(Dispenser<?> dispenser) { return dispenser.next(); }   // the bound survives the ?
    static Object peek(Box<?> box) { return box.item; }

    public static void main(String[] args) {
        Dispenser<Apple> apples = () -> new Apple("Gala", 180);
        Bin<Fruit> compost = item -> System.out.println("compost: " + item);
        Box<Integer> box = new Box<>(180);

        System.out.println("peek(dispenser) = " + peek(apples) + ", peek(box) = " + peek(box));

        compost.drop(new Lemon("Eureka", 95));      // through the real type: fine
        Bin<?> someBin = compost;                   // through ?: only null can be dropped in
        someBin.drop(null);                         // Java lets null through a ?; Kotlin's * does not
        Box<?> someBox = box;
        System.out.println("a Box<?> still reads: " + someBox.item);

        // Wrong moves. Uncomment one at a time, predict the error, then run.
        // someBin.drop(new Apple("Fuji", 150));   // 1
        // someBox.item = 150;                     // 2
        // Apple a = peek(apples);                 // 3
    }
}
