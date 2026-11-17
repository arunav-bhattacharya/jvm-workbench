package workbench.generics.l08.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ErasureDemo.kt. Java erases type arguments in exactly the same way. */
public class ErasureDemoJava {

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        // 1. Two different types, one class at run time.
        List<String> varieties = new ArrayList<>();
        List<Integer> weights = new ArrayList<>();
        System.out.println("same class at run time: " + (varieties.getClass() == weights.getClass()) + " (" + varieties.getClass().getName() + ")");

        // 2. An unchecked cast succeeds, because only the class can be checked.
        List<String> lies = (List<String>) (Object) List.of(180, 150);
        System.out.println("the cast worked, size = " + lies.size());

        // 3. The failure comes later, where a String is finally needed.
        try {
            String first = lies.get(0);
            System.out.println(first);
        } catch (ClassCastException e) {
            System.out.println("ClassCastException at the read: " + e.getMessage().split(" \\(")[0]);
        }

        // Wrong move 1. Uncomment, predict the error, then run.
        // System.out.println(((Object) varieties) instanceof List<String>);
    }

    // Wrong move 2: make a T without knowing what T is.
    // static <T> T make() { return new T(); }
}
