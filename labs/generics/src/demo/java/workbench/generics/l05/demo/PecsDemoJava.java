package workbench.generics.l05.demo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Java twin of PecsDemo.kt. Producer extends, consumer super: the JDK's own copy has both. */
public class PecsDemoJava {

    // the same shape as java.util.Collections.copy(List<? super T> dest, List<? extends T> src)
    static <T> void copyInto(List<? extends T> from, List<? super T> to) {
        for (T x : from) to.add(x);
    }

    public static void main(String[] args) {
        List<Integer> amounts = List.of(1_200, 350);
        List<Number> numbers = new ArrayList<>(List.of(2.5));
        List<Object> anything = new ArrayList<>(List.of("EUR"));

        copyInto(amounts, numbers);       // T = Integer, or Number: both work
        copyInto(amounts, anything);
        System.out.println("numbers = " + numbers + ", anything = " + anything);

        List<Number> slots = new ArrayList<>(Collections.nCopies(2, 0));
        Collections.copy(slots, amounts);  // the JDK version overwrites slots in place
        System.out.println("slots = " + slots);

        // Wrong move. Uncomment, predict the error, then run.
        // copyInto(numbers, new ArrayList<Integer>());
    }
}
