package workbench.generics.l06.demo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Java twin of WriteViewDemo.kt. ? super at the use site is Kotlin's in-projection. */
public class WriteViewDemoJava {

    static void padWithZeros(List<? super Integer> target, int count) {
        for (int i = 0; i < count; i++) target.add(0);    // writing an Integer: fine
        Object first = target.isEmpty() ? null : target.get(0);   // reading compiles, as Object
        System.out.println("  first is " + first);
        // Integer firstInt = target.get(0);              // wrong move 1: ? super can't promise an Integer
    }

    public static void main(String[] args) {
        List<Integer> ints = new ArrayList<>(List.of(1_200));
        List<Number> numbers = new ArrayList<>(List.of(2.5));
        List<Object> anything = new ArrayList<>(List.of("EUR"));
        padWithZeros(ints, 1);
        padWithZeros(numbers, 2);
        padWithZeros(anything, 2);
        System.out.println("ints = " + ints + ", numbers = " + numbers + ", anything = " + anything);

        Collections.fill(numbers, 7);                      // fill(List<? super T> list, T obj)
        System.out.println("after Collections.fill: " + numbers);

        // Wrong move 2: a list of Doubles can't take an Integer.
        // padWithZeros(new ArrayList<Double>(List.of(0.5)), 1);
    }
}
