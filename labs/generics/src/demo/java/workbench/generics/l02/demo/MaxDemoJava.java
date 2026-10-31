package workbench.generics.l02.demo;

import java.time.LocalDate;

/** Java twin of MaxDemo.kt. The bound T extends Comparable<T> makes compareTo available. */
public class MaxDemoJava {

    static <T extends Comparable<T>> T maxOf2(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    // the JDK's own style: LocalDate is a Comparable<ChronoLocalDate>, not a Comparable<LocalDate>,
    // so only this version can return a LocalDate
    static <T extends Comparable<? super T>> T maxOf2Flexible(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    record Payment(String id, long cents) {}

    public static void main(String[] args) {
        System.out.println(maxOf2(1_200, 99));
        System.out.println(maxOf2("EUR", "USD"));
        System.out.println(maxOf2Flexible(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30)));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // System.out.println(maxOf2(1, "a"));
        // System.out.println(maxOf2(new Payment("pay_1", 500), new Payment("pay_2", 900)));
        // LocalDate later = maxOf2(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30));
    }
}
