package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of InvarianceDemo.kt. What would go wrong if List<String> were a List<Object>? */
public class InvarianceDemoJava {
    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        List<String> ids = new ArrayList<>(List.of("pay_1"));

        // Step 1: uncomment this line and run. javac refuses it.
        // List<Object> view = ids;

        // Step 2: force it through a raw type. This compiles, with an unchecked warning.
        List<Object> anything = (List<Object>) (List<?>) ids;
        anything.add(42);                         // fine for a List<Object>
        System.out.println("ids has " + ids.size() + " elements, and nothing failed yet");

        try {
            String second = ids.get(1);           // javac inserted a cast to String here
            System.out.println("second id: " + second);
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
    }
}
