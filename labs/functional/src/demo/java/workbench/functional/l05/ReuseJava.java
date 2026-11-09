package workbench.functional.l05;

import java.util.List;
import java.util.stream.Stream;

/** A Java Stream is always single-use: the second terminal operation throws. */
public class ReuseJava {
    record Refund(int id, long amountCents) {}

    public static void main(String[] args) {
        List<Refund> refunds = List.of(new Refund(1, 500), new Refund(2, 1_200), new Refund(3, 300));

        Stream<Long> amounts = refunds.stream().map(r -> { System.out.println("  map " + r.id()); return r.amountCents(); });
        System.out.println("sum = " + amounts.mapToLong(Long::longValue).sum());
        try {
            System.out.println("count = " + amounts.count());
        } catch (IllegalStateException e) {
            System.out.println("count again: " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        // to run it again, build a new stream from the source
        System.out.println("count = " + refunds.stream().count());
    }
}
