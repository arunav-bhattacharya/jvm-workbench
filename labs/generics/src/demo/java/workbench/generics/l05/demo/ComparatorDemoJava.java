package workbench.generics.l05.demo;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** Java twin of ComparatorDemo.kt. List.sort takes a Comparator<? super E>. */
public class ComparatorDemoJava {

    static final Comparator<Fruit> BY_WEIGHT = Comparator.comparingInt(Fruit::getGrams);

    static List<String> show(List<? extends Fruit> fruit) {
        return fruit.stream().map(f -> f.getName() + " " + f.getGrams() + " g").toList();
    }

    public static void main(String[] args) {
        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala", 180), new Apple("Fuji", 150)));
        List<Lemon> lemons = new ArrayList<>(List.of(new Lemon("Eureka", 120), new Lemon("Eureka", 95)));

        List<Apple> sortedApples = new ArrayList<>(apples);
        sortedApples.sort(BY_WEIGHT);     // List<E>.sort(Comparator<? super E>)
        List<Lemon> sortedLemons = new ArrayList<>(lemons);
        sortedLemons.sort(BY_WEIGHT);
        System.out.println(show(sortedApples));
        System.out.println(show(sortedLemons));

        Comparator<? super Apple> forApples = BY_WEIGHT;

        // Wrong move. Uncomment, predict the error, then run.
        // Comparator<Apple> strict = BY_WEIGHT;
        System.out.println("forApples compares Gala with Fuji: " + forApples.compare(apples.get(0), apples.get(1)));
    }
}
