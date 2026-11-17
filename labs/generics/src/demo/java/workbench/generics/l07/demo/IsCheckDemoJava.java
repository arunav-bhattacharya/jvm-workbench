package workbench.generics.l07.demo;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Java twin of IsCheckDemo.kt. instanceof works with List<?> and Map<?, ?>, not with List<Integer>. */
public class IsCheckDemoJava {

    static String shape(Object note) {
        if (note == null) return "empty";
        if (note instanceof Map<?, ?> map) return "a map with keys " + map.keySet();
        if (note instanceof List<?> list) return "a list of " + list.size();
        return "a single value: " + note;
    }

    static List<Integer> weightsIn(Object note) {
        List<Integer> out = new ArrayList<>();
        if (note instanceof List<?> list) {
            for (Object e : list) if (e instanceof Integer i) out.add(i);   // check every element
        }
        return out;
    }

    public static void main(String[] args) {
        Map<String, Object> fields = new LinkedHashMap<>();    // keeps key order, like Kotlin's mapOf
        fields.put("supplier", "Hillside Orchard");
        fields.put("weights", List.of(180, "bruised", 150));
        Object note = fields;
        System.out.println(shape(note));
        System.out.println(shape(List.of(1, 2, 3)));
        System.out.println(shape(42));

        Object weights = ((Map<?, ?>) note).get("weights");
        System.out.println("weights = " + weightsIn(weights));

        // Wrong move. Uncomment, predict the error, then run.
        // if (weights instanceof List<Integer>) System.out.println("a list of weights");
    }
}
