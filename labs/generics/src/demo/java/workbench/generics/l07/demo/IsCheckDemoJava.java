package workbench.generics.l07.demo;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Java twin of IsCheckDemo.kt. instanceof works with List<?> and Map<?, ?>, not with List<Long>. */
public class IsCheckDemoJava {

    static String shape(Object payload) {
        if (payload == null) return "empty";
        if (payload instanceof Map<?, ?> map) return "object with keys " + map.keySet();
        if (payload instanceof List<?> list) return "array of " + list.size();
        return "value " + payload;
    }

    static List<Long> amountsIn(Object payload) {
        List<Long> out = new ArrayList<>();
        if (payload instanceof List<?> list) {
            for (Object e : list) if (e instanceof Long l) out.add(l);   // check every element
        }
        return out;
    }

    public static void main(String[] args) {
        Map<String, Object> fields = new LinkedHashMap<>();    // keeps key order, like Kotlin's mapOf
        fields.put("id", "pay_1");
        fields.put("amounts", List.of(1_200L, "oops", 350L));
        Object webhook = fields;
        System.out.println(shape(webhook));
        System.out.println(shape(List.of(1, 2, 3)));
        System.out.println(shape(42));

        Object amounts = ((Map<?, ?>) webhook).get("amounts");
        System.out.println("amounts = " + amountsIn(amounts));

        // Wrong move. Uncomment, predict the error, then run.
        // if (amounts instanceof List<Long>) System.out.println("a list of longs");
    }
}
