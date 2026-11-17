package workbench.generics.l08.demo;

import java.util.Arrays;
import java.util.List;

/**
 * Java twin of ReifiedDemo.kt. Java has no reified type parameters. The closest Java equivalent
 * is to pass the Class object yourself and use isInstance and cast.
 * Fruit, Apple and Lemon are the Kotlin types from ReifiedDemo.kt.
 */
public class ReifiedDemoJava {

    static boolean isA(Object x, Class<?> type) { return type.isInstance(x); }

    static <T> List<T> filterIsInstance(List<?> items, Class<T> type) {
        return items.stream().filter(type::isInstance).map(type::cast).toList();
    }

    static String nameOf(Class<?> type) { return type.getSimpleName(); }

    public static void main(String[] args) {
        List<Object> delivery = Arrays.asList(new Apple("Gala", 180), "a paper bag", null, new Lemon("Eureka", 120), new Apple("Fuji", 150));

        System.out.println("Gala isA(Apple.class) = " + isA(delivery.get(0), Apple.class) + ", the bag isA(Apple.class) = " + isA(delivery.get(1), Apple.class));
        System.out.println("apples: " + filterIsInstance(delivery, Apple.class));
        System.out.println("lemons: " + filterIsInstance(delivery, Lemon.class));
        System.out.println("nameOf(Lemon.class) = " + nameOf(Lemon.class));
    }

    // Wrong move. Uncomment, predict the error, then run.
    // static <T> boolean isErased(Object x) { return x instanceof T; }
}
