package workbench.functional.l05.demo;

import java.util.List;
import java.util.stream.Stream;

/** A Java Stream is always single-use: the second terminal operation throws. */
public class ReuseJava {
    record Item(String name, int grams) {}

    public static void main(String[] args) {
        List<Item> basket = List.of(new Item("flour", 500), new Item("sugar", 200), new Item("butter", 250));

        Stream<Integer> weights = basket.stream().map(i -> { System.out.println("  weigh " + i.name()); return i.grams(); });
        System.out.println("sum = " + weights.mapToInt(Integer::intValue).sum());
        try {
            System.out.println("count = " + weights.count());
        } catch (IllegalStateException e) {
            System.out.println("count again: " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        // to run it again, build a new stream from the source
        System.out.println("count = " + basket.stream().count());
    }
}
