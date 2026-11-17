package workbench.functional.l03.demo;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/** Java twin of Memoize.kt. */
public class MemoizeJava {

    // A higher-order method that returns a function: same answers as f, but each one computed once.
    static <A, R> Function<A, R> memoize(Function<A, R> f) {
        Map<A, R> cache = new ConcurrentHashMap<>();          // captured: one cache per memoized function
        return a -> cache.computeIfAbsent(a, f);
    }

    // Pure but slow: imagine it searches a long food table on every call.
    static int tableLookups = 0;
    static int kcalPer100g(String food) {
        tableLookups++;
        try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return food.equals("oats") ? 389 : 304;
    }

    // Impure: the number of eggs changes whenever someone cooks.
    static int fridgeEggs = 6;
    static int eggsIn(String place) { return place.equals("fridge") ? fridgeEggs : 0; }

    public static void main(String[] args) {
        Function<String, Integer> kcal = memoize(MemoizeJava::kcalPer100g);
        List<String> foods = List.of("oats", "honey", "oats", "oats", "honey");
        long start = System.nanoTime();
        System.out.println(foods.stream().map(kcal).toList());
        System.out.printf("lookups: %d for %d calls, %d ms%n", tableLookups, foods.size(), (System.nanoTime() - start) / 1_000_000);

        Function<String, Integer> eggs = memoize(MemoizeJava::eggsIn);
        System.out.println("eggs in the fridge now:        " + eggs.apply("fridge"));
        fridgeEggs = 2;                                       // someone makes an omelette
        System.out.println("eggs after someone's omelette: " + eggs.apply("fridge") + "   (really: " + eggsIn("fridge") + ")");
    }
}
