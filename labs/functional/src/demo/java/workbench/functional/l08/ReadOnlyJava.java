package workbench.functional.l08;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** The same traps in Java: views that change, shallow records, and BigDecimal.equals. */
public class ReadOnlyJava {
    record Batch(String id, List<String> paymentIds) {}
    record Fee(String merchantId, BigDecimal amount) {}

    public static void main(String[] args) {
        // 1. a record holding the caller's list sees every later change
        List<String> backing = new ArrayList<>(List.of("p1"));
        Batch batch = new Batch("b-7", backing);
        backing.add("p2");
        System.out.println("1. batch after the caller adds p2: " + batch.paymentIds());

        // 2. Collections.unmodifiableList is a view too: it blocks writes through it, not changes behind it
        List<String> view = Collections.unmodifiableList(backing);
        backing.add("p3");
        System.out.println("2. unmodifiable view:             " + view);

        // 3. List.copyOf takes a real snapshot (JDK 10+) and rejects writes
        Batch safe = new Batch("b-8", List.copyOf(backing));
        backing.add("p4");
        System.out.println("3. snapshot after another add:    " + safe.paymentIds());
        try {
            safe.paymentIds().add("p5");
        } catch (UnsupportedOperationException e) {
            System.out.println("   add: UnsupportedOperationException");
        }

        // 4. BigDecimal.equals compares the scale, and record equals uses it
        System.out.println("4. Fee(10.00).equals(Fee(10.0)): "
                + new Fee("m-1", new BigDecimal("10.00")).equals(new Fee("m-1", new BigDecimal("10.0"))));
        System.out.println("   compareTo says equal: " + (new BigDecimal("10.00").compareTo(new BigDecimal("10.0")) == 0));
    }
}
