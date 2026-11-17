package workbench.generics.l02.demo;

import java.time.LocalDate;

/** Java twin of MaxDemo.kt. A bound written with extends makes the bound's methods available. */
public class MaxDemoJava {

    interface Fruit { String name(); int grams(); }
    record Apple(String name, int grams) implements Fruit {}

    static <T extends Fruit> T heavier(T a, T b) {
        return a.grams() >= b.grams() ? a : b;
    }

    static <T extends Comparable<T>> T maxOf2(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    // the JDK's own style: LocalDate is a Comparable<ChronoLocalDate>, not a Comparable<LocalDate>,
    // so only this version can return a LocalDate
    static <T extends Comparable<? super T>> T maxOf2Flexible(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    public static void main(String[] args) {
        Apple apple = heavier(new Apple("Gala", 180), new Apple("Fuji", 150));   // two apples in, an Apple out
        System.out.println(apple);
        System.out.println(maxOf2(180, 150));
        System.out.println(maxOf2("Gala", "Fuji"));
        System.out.println(maxOf2Flexible(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30)));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // System.out.println(heavier("Gala", "Fuji"));
        // System.out.println(maxOf2(1, "a"));
        // System.out.println(maxOf2(new Apple("Gala", 180), new Apple("Fuji", 150)));
        // LocalDate later = maxOf2(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30));
    }
}
