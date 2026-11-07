package workbench.generics.l06.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ReadViewDemo.kt. ? extends at the use site is Kotlin's out-projection. */
public class ReadViewDemoJava {

    static double total(List<? extends Number> amounts) {
        double sum = 0;
        for (Number a : amounts) sum += a.doubleValue();   // reads come out as Number
        // amounts.add(0);                                // wrong move 1: no add() through ? extends
        return sum;
    }

    public static void main(String[] args) {
        List<Integer> cents = new ArrayList<>(List.of(1_200, 350, 99));
        List<Double> rates = new ArrayList<>(List.of(0.5, 1.25));
        System.out.println("cents: " + total(cents) + ", rates: " + total(rates));

        List<? extends Number> view = cents;               // the same wildcard on a variable
        view.remove(0);                                    // still allowed: remove(int) takes no T
        System.out.println("after remove through the view: " + cents);

        // Wrong move 2: no wildcard, so a List<Integer> is not a List<Number>.
        // List<Number> strict = cents;
    }
}
