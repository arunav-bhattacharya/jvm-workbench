package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java arrays are covariant, so the JVM must check every store. Java generics are invariant instead. */
public class ArrayStoreDemo {
    public static void main(String[] args) {
        String[] currencies = { "EUR", "USD" };
        Object[] objects = currencies;           // compiles: a String[] is an Object[]
        try {
            objects[0] = 978;                    // compiles too: an Integer is an Object
            System.out.println("stored 978");
        } catch (ArrayStoreException e) {
            System.out.println("ArrayStoreException: " + e.getMessage());
        }

        List<String> names = new ArrayList<>(List.of("EUR"));
        // Step 2: uncomment the next line and run. javac refuses it.
        // List<Object> objectList = names;
        System.out.println("currencies[0] is still " + currencies[0]);
    }
}
