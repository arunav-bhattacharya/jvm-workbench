package workbench.generics.l10.demo;

import java.util.Arrays;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Objects;

/**
 * Java twin of NonNullDemo.kt. Java types say nothing about null, so "T, but not null" can only be
 * a convention (or an annotation such as @NotNull), checked at run time.
 */
public class NonNullDemoJava {

    static <T> T firstNotNullValue(List<T> items) {
        for (T item : items) if (item != null) return item;
        throw new NoSuchElementException("no non-null element");
    }

    static <T> T elvis(T x, T y) { return x != null ? x : Objects.requireNonNull(y); }

    public static void main(String[] args) {
        List<String> currencies = Arrays.asList(null, "eur", "usd");
        String first = firstNotNullValue(currencies);
        String shown = elvis(null, "no note");
        System.out.println("first = " + first + ", shown = " + shown);
        System.out.println("transformed = " + new UpperCaser<String>().transform("pay_1"));

        // Uncomment and run: it compiles in Java. What happens at run time?
        // String oops = elvis(null, null);
    }
}
