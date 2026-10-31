package workbench.generics.l03.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ClassVsTypeDemo.kt. Classes exist at run time; types are what javac checks. */
public class ClassVsTypeDemoJava {
    public static void main(String[] args) {
        List<String> ids = new ArrayList<>(List.of("pay_1"));
        List<Integer> amounts = new ArrayList<>(List.of(1200));

        // the JVM sees one class for both lists
        System.out.println("same runtime class:  " + (ids.getClass() == amounts.getClass()) + "  (" + ids.getClass().getName() + ")");
        // Java has one List interface; there is no read-only List type to compare it with
        System.out.println("List.class:  " + List.class);

        // Java types carry no nullability: every String variable may hold null
        String maybe = ids.isEmpty() ? null : ids.get(0);
        String sure = "EUR";
        String widened = sure;
        System.out.println("maybe holds '" + maybe + "', widened holds '" + widened + "'");

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // String narrowed = maybe;
        // Class<List<String>> k = List.class;
    }
}
