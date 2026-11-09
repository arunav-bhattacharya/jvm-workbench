package workbench.functional.l05;

import java.util.List;

/**
 * The same three steps in Java. Java has no eager chain, so the "List chain" collects after every step,
 * which is exactly what Kotlin's List operations do. A Stream works like a Kotlin Sequence.
 */
public class OrderDemoJava {
    enum Status { SETTLED, PENDING, FAILED }

    record Txn(int id, String merchant, long amountCents, Status status) {}

    static final List<Txn> TXNS = List.of(
            new Txn(1, "acme", 1_500, Status.SETTLED),
            new Txn(2, "globex", 9_900, Status.PENDING),
            new Txn(3, "acme", 2_000, Status.SETTLED),
            new Txn(4, "initech", 12_000, Status.FAILED),
            new Txn(5, "globex", 700, Status.SETTLED));

    public static void main(String[] args) {
        System.out.println("Collect after every step:");
        List<Txn> settled = TXNS.stream()
                .filter(t -> { System.out.println("  filter " + t.id()); return t.status() == Status.SETTLED; })
                .toList();
        List<Long> amounts = settled.stream()
                .map(t -> { System.out.println("  map " + t.id()); return t.amountCents(); })
                .toList();
        System.out.println("  result " + amounts.stream().limit(2).toList());

        System.out.println("One Stream:");
        var stream = TXNS.stream()
                .filter(t -> { System.out.println("  filter " + t.id()); return t.status() == Status.SETTLED; })
                .map(t -> { System.out.println("  map " + t.id()); return t.amountCents(); })
                .limit(2);
        System.out.println("  built a stream, nothing has run yet");
        System.out.println("  result " + stream.toList());
    }
}
