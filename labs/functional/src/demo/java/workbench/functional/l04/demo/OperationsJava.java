package workbench.functional.l04.demo;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/** Java twin of Operations.kt: the same operations on streams. */
public class OperationsJava {

    enum Status { SETTLED, PENDING, FAILED }
    record Payment(String id, String merchant, long amountCents, Status status, Long refundCents) {}

    static final List<Payment> DAY = List.of(
            new Payment("pay_1", "acme", 1_500, Status.SETTLED, null),
            new Payment("pay_2", "globex", 9_900, Status.PENDING, null),
            new Payment("pay_3", "acme", 2_000, Status.SETTLED, 500L),
            new Payment("pay_4", "initech", 12_000, Status.FAILED, null),
            new Payment("pay_5", "globex", 700, Status.SETTLED, null));

    public static void main(String[] args) {
        System.out.println("map:         " + DAY.stream().map(Payment::amountCents).toList());
        System.out.println("filter:      " + DAY.stream().filter(p -> p.status() == Status.SETTLED).map(Payment::id).toList());
        System.out.println("mapNotNull:  " + DAY.stream().map(Payment::refundCents).filter(Objects::nonNull).toList());

        List<List<Payment>> batches = List.of(DAY.subList(0, 3), DAY.subList(3, 5));   // two acquirer files
        System.out.println("flatMap:     " + batches.stream().flatMap(b -> b.stream().map(Payment::id)).toList());

        System.out.println("sumOf:       " + DAY.stream().mapToLong(Payment::amountCents).sum());
        System.out.println("count:       " + DAY.stream().filter(p -> p.status() == Status.SETTLED).count());
        System.out.println("any / all:   " + DAY.stream().anyMatch(p -> p.amountCents() > 10_000)
                + " / " + DAY.stream().allMatch(p -> p.amountCents() > 0));

        Map<Boolean, List<String>> split = DAY.stream().collect(Collectors.partitioningBy(
                p -> p.status() == Status.SETTLED, Collectors.mapping(Payment::id, Collectors.toList())));
        System.out.println("partition:   " + split.get(true) + " / " + split.get(false));

        System.out.println("toList returns: " + DAY.stream().map(Payment::id).toList().getClass().getName());
    }
}
