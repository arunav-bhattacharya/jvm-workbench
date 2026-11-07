package workbench.generics.l07.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of StarVsAnyDemo.kt, plus the thing Kotlin does not have: a raw type.
 * List<Object> is "a list of anything". List<?> is "a list of something". Raw List is "don't check".
 */
public class StarVsAnyDemoJava {

    static void addMarker(List<Object> list) { list.add("marker"); }

    static int sizeOf(List<?> list) { return list.size(); }

    @SuppressWarnings({"rawtypes", "unchecked"})
    static void addRaw(List list) { list.add(42); }       // raw: the compiler stops checking

    public static void main(String[] args) {
        List<Object> anything = new ArrayList<>(List.of(1_200, "EUR"));
        List<String> ids = new ArrayList<>(List.of("pay_1"));

        addMarker(anything);
        System.out.println("anything = " + anything + ", sizeOf(ids) = " + sizeOf(ids));

        addRaw(ids);                                       // compiles: an Integer goes into a List<String>
        System.out.println("ids = " + ids + " (looks fine so far)");
        try {
            String last = ids.get(1);                      // the failure shows up here, far from addRaw
            System.out.println(last);
        } catch (ClassCastException e) {
            System.out.println("ClassCastException at the read: " + e.getMessage());
        }

        // Wrong move. Uncomment, predict the error, then run.
        // addMarker(ids);
    }
}
