package workbench.generics.l10.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of UnsafeVarianceDemo.kt. Java's contains takes an Object, so it never needed the
 * annotation, and it can't catch a nonsense check. Java's way to break a ? extends view on purpose
 * is an unchecked cast.
 */
public class UnsafeVarianceDemoJava {

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        List<? extends Number> amounts = List.of(1_200, 350);
        System.out.println("contains(350): " + amounts.contains(350) + ", contains(2.5): " + amounts.contains(2.5));

        System.out.println("contains(\"1200\") compiles in Java: " + List.of(1_200, 350).contains("1200"));

        List<String> ids = new ArrayList<>(List.of("pay_1"));
        List<? extends Object> view = ids;
        ((List<Object>) view).add(42);                     // the unchecked cast is the Java "unsafe variance"
        try {
            String lastId = ids.get(ids.size() - 1);
            System.out.println(lastId);
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage().split(" \\(")[0]);
        }
    }
}
