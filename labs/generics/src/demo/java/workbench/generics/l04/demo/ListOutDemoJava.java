package workbench.generics.l04.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of ListOutDemo.kt. Java writes the read-only view as List<? extends Fruit> at each use.
 * It also calls the Kotlin function totalWeight: Kotlin compiled its List<Fruit> parameter as
 * List<? extends Fruit>, because Kotlin's List is declared `out`. Fruit and Apple come from ProducerDemo.kt.
 */
public class ListOutDemoJava {

    static int totalWeightJava(List<? extends Fruit> fruit) {
        int sum = 0;
        for (Fruit f : fruit) sum += f.getGrams();
        return sum;
    }

    static int totalWeightInvariant(List<Fruit> fruit) {
        return totalWeightJava(fruit);
    }

    public static void main(String[] args) {
        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala", 180), new Apple("Fuji", 150)));
        System.out.println("totalWeightJava(apples) = " + totalWeightJava(apples));
        System.out.println("Kotlin's totalWeight(apples) from Java = " + ListOutDemoKt.totalWeight(apples));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // System.out.println(totalWeightInvariant(apples));
        // System.out.println(ListOutDemoKt.totalWeightMutable(apples));
    }
}
