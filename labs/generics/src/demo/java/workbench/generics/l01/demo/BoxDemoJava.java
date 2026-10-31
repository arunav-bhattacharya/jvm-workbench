package workbench.generics.l01.demo;

import java.util.List;

/** Java twin of BoxDemo.kt: one class with one blank, T. */
public class BoxDemoJava {

    static class Box<T> {
        private T value;
        Box(T value) { this.value = value; }
        T get() { return value; }

        /** Puts newValue in and returns the old value. Both have type T. */
        T replace(T newValue) {
            T old = value;
            value = newValue;
            return old;
        }
    }

    /** A generic method: <T> before the return type declares the blank. */
    static <T> T firstOrNull(List<T> items) {
        return items.isEmpty() ? null : items.get(0);
    }

    public static void main(String[] args) {
        Box<String> currency = new Box<>("EUR");     // diamond: javac infers <String>
        Box<Long> limit = new Box<>(50_000L);
        String old = currency.replace("USD");
        System.out.println("currency was " + old + ", now " + currency.get());
        System.out.println("limit is " + limit.get());
        System.out.println("first payment id: " + firstOrNull(List.of("pay_1", "pay_2")));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // limit.replace("USD");
        // Box<String> wrong = new Box<>(42);
        // String id = firstOrNull(List.<String>of());
    }
}
