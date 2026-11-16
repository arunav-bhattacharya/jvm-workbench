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
        Box<String> variety = new Box<>("Gala");     // diamond: javac infers <String>
        Box<Integer> count = new Box<>(12);
        String old = variety.replace("Fuji");
        System.out.println("variety was " + old + ", now " + variety.get());
        System.out.println("count is " + count.get());
        System.out.println("first on the list: " + firstOrNull(List.of("Gala", "Fuji")));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // count.replace("Fuji");
        // Box<String> wrong = new Box<>(42);
        // String first = firstOrNull(List.<String>of());
    }
}
