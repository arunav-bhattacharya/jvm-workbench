package workbench.generics.l08.demo;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.List;

/**
 * Java twin of ReifiedDemo.kt. Java has no reified type parameters. The closest Java equivalent
 * is to pass the Class object yourself and use isInstance and cast.
 */
public class ReifiedDemoJava {

    static boolean isA(Object x, Class<?> type) { return type.isInstance(x); }

    static <T> List<T> filterIsInstance(List<?> items, Class<T> type) {
        return items.stream().filter(type::isInstance).map(type::cast).toList();
    }

    static String nameOf(Class<?> type) { return type.getSimpleName(); }

    public static void main(String[] args) {
        List<Object> payload = Arrays.asList("pay_1", 1_200L, null, "pay_2", 2.5);

        System.out.println("isA(\"pay_1\", String.class) = " + isA("pay_1", String.class) + ", isA(1200L, String.class) = " + isA(1_200L, String.class));
        System.out.println("strings: " + filterIsInstance(payload, String.class));
        System.out.println("longs:   " + filterIsInstance(payload, Long.class));
        System.out.println("nameOf(BigDecimal.class) = " + nameOf(BigDecimal.class));
    }

    // Wrong move. Uncomment, predict the error, then run.
    // static <T> boolean isErased(Object x) { return x instanceof T; }
}
