package workbench.generics.l06.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ReadViewDemo.kt. ? extends at the use site is Kotlin's out-projection. */
public class ReadViewDemoJava {

    static int totalGrams(List<? extends Fruit> crate) {
        int sum = 0;
        for (Fruit f : crate) sum += f.getGrams();         // reads come out as Fruit
        // crate.add(new Apple("Gala", 180));             // wrong move 1: no add() through ? extends
        return sum;
    }

    public static void main(String[] args) {
        List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala", 180), new Apple("Fuji", 150)));
        List<Lemon> lemons = new ArrayList<>(List.of(new Lemon("Eureka", 120)));
        System.out.println("apples: " + totalGrams(apples) + " g, lemons: " + totalGrams(lemons) + " g");

        List<? extends Fruit> view = apples;               // the same wildcard on a variable
        view.remove(0);                                    // still allowed: remove(int) takes no T
        System.out.println("after remove through the view: " + apples);

        // Wrong move 2: no wildcard, so a List<Apple> is not a List<Fruit>.
        // List<Fruit> strict = apples;
    }
}
