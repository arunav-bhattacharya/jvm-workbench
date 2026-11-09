package workbench.functional.l04.demo;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/** Java twin of ReportLoop.kt: the report as one loop, then as streams. */
public class ReportLoopJava {

    enum Status { SETTLED, PENDING, FAILED }
    record Payment(String id, String merchant, long amountCents, Status status, Long refundCents) {}

    static final List<Payment> DAY = List.of(
            new Payment("pay_1", "acme", 1_500, Status.SETTLED, null),
            new Payment("pay_2", "globex", 9_900, Status.PENDING, null),
            new Payment("pay_3", "acme", 2_000, Status.SETTLED, 500L),
            new Payment("pay_4", "initech", 12_000, Status.FAILED, null),
            new Payment("pay_5", "globex", 700, Status.SETTLED, null));

    static long refundOf(Payment p) { return p.refundCents() == null ? 0 : p.refundCents(); }

    // The loop: four results built at once, and every line changes one of them.
    static String reportLoop(List<Payment> payments) {
        long settled = 0;
        Map<String, Long> net = new LinkedHashMap<>();
        List<String> failed = new ArrayList<>();
        Payment largest = payments.get(0);
        for (Payment p : payments) {
            switch (p.status()) {
                case SETTLED -> {
                    settled += p.amountCents();
                    net.merge(p.merchant(), p.amountCents() - refundOf(p), Long::sum);
                    if (p.amountCents() > largest.amountCents()) largest = p;
                }
                case FAILED -> failed.add(p.id());
                case PENDING -> { }
            }
        }
        return "settled=" + settled + " net=" + net + " failed=" + failed + " largest=" + largest.id();
    }

    // The same report with streams. groupingBy needs LinkedHashMap::new to keep first-seen order.
    static String reportChain(List<Payment> payments) {
        List<Payment> settledPayments = payments.stream().filter(p -> p.status() == Status.SETTLED).toList();
        long settled = settledPayments.stream().mapToLong(Payment::amountCents).sum();
        Map<String, Long> net = settledPayments.stream().collect(Collectors.groupingBy(
                Payment::merchant, LinkedHashMap::new, Collectors.summingLong(p -> p.amountCents() - refundOf(p))));
        List<String> failed = payments.stream().filter(p -> p.status() == Status.FAILED).map(Payment::id).toList();
        String largest = settledPayments.stream()
                .max(Comparator.comparingLong(Payment::amountCents))
                .map(Payment::id).orElse(null);
        return "settled=" + settled + " net=" + net + " failed=" + failed + " largest=" + largest;
    }

    public static void main(String[] args) {
        List<Payment> payments = args.length > 0 && args[0].equals("empty") ? List.of() : DAY;
        System.out.println("chain: " + reportChain(payments));
        try {
            System.out.println("loop:  " + reportLoop(payments));
        } catch (IndexOutOfBoundsException e) {
            System.out.println("loop:  threw " + e);
        }
    }
}
