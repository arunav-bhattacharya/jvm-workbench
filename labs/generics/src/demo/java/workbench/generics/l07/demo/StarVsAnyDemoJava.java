package workbench.generics.l07.demo;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Java twin of StarVsAnyDemo.kt, plus the thing Kotlin does not have: a raw type.
 * List<Object> is "a list of anything". List<?> is "a list of something". Raw List is "don't check".
 */
public class StarVsAnyDemoJava {

    static void addPriceTag(List<Object> list) { list.add("price tag"); }

    static int countItems(List<?> list) { return list.size(); }

    @SuppressWarnings({"rawtypes", "unchecked"})
    static void addRaw(List list) { list.add(42); }        // raw: the compiler stops checking

    public static void main(String[] args) {
        List<Object> drawer = new ArrayList<>(Arrays.asList("pencil", 3, null));   // the drawer of odds and ends
        List<String> varieties = new ArrayList<>(List.of("Gala"));

        addPriceTag(drawer);
        System.out.println("drawer = " + drawer + ", countItems(varieties) = " + countItems(varieties));

        addRaw(varieties);                                  // compiles: an Integer goes into a List<String>
        System.out.println("varieties = " + varieties + " (looks fine so far)");
        try {
            String last = varieties.get(1);                 // the failure shows up here, far from addRaw
            System.out.println(last);
        } catch (ClassCastException e) {
            System.out.println("ClassCastException at the read: " + e.getMessage());
        }

        // Wrong move. Uncomment, predict the error, then run.
        // addPriceTag(varieties);
    }
}
