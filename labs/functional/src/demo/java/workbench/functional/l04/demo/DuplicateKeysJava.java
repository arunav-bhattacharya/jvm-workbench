package workbench.functional.l04.demo;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/** Java twin of DuplicateKeys.kt. Same data, different defaults: no key order, and toMap throws. */
public class DuplicateKeysJava {

    enum Status { SETTLED, PENDING, FAILED }
    record Payment(String id, String merchant, long amountCents, Status status, Long refundCents) {}

    static final List<Payment> DAY = List.of(
            new Payment("pay_1", "acme", 1_500, Status.SETTLED, null),
            new Payment("pay_2", "globex", 9_900, Status.PENDING, null),
            new Payment("pay_3", "acme", 2_000, Status.SETTLED, 500L),
            new Payment("pay_4", "initech", 12_000, Status.FAILED, null),
            new Payment("pay_5", "globex", 700, Status.SETTLED, null));

    public static void main(String[] args) {
        Map<String, List<String>> byMerchant = DAY.stream().collect(
                Collectors.groupingBy(Payment::merchant, Collectors.mapping(Payment::id, Collectors.toList())));
        System.out.println("groupingBy:   " + byMerchant);
        System.out.println("map class:    " + byMerchant.getClass().getName());

        // One value per key. acme and globex each have two payments.
        try {
            System.out.println("toMap:        " + DAY.stream().collect(Collectors.toMap(Payment::merchant, Payment::id)));
        } catch (IllegalStateException e) {
            System.out.println("toMap:        threw " + e);
        }

        // Counting per key.
        System.out.println("counting:     " + DAY.stream().collect(
                Collectors.groupingBy(Payment::merchant, Collectors.counting())));
    }
}
