package workbench.modernjava.l01.demo;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Equality, hashCode and toString are only as deep as the components. */
public class ShallowDemo {

    record Batch(String id, List<String> paymentIds) {}

    record SafeBatch(String id, List<String> paymentIds) {
        SafeBatch { paymentIds = List.copyOf(paymentIds); }       // unmodifiable copy
    }

    record Masked(String card) {
        @Override
        public String card() { return "****" + card.substring(card.length() - 4); }
    }

    record Rate(double value) {}

    public static void main(String[] args) {
        List<String> ids = new ArrayList<>(List.of("pay_1", "pay_2"));
        Batch batch = new Batch("b-7", ids);
        Set<Batch> sent = new HashSet<>(Set.of(batch));
        int before = batch.hashCode();

        ids.add("pay_3");                                         // someone reuses their list

        System.out.println("batch now:          " + batch);
        System.out.println("hashCode changed:   " + (before != batch.hashCode()));
        System.out.println("sent.contains:      " + sent.contains(batch));

        List<String> ids2 = new ArrayList<>(List.of("pay_1", "pay_2"));
        SafeBatch safe = new SafeBatch("b-8", ids2);
        ids2.add("pay_3");
        System.out.println("safe batch:         " + safe);

        Masked m = new Masked("4111111111111111");
        System.out.println("accessor:           " + m.card());
        System.out.println("toString:           " + m);
        System.out.println("copy equals orig:   " + new Masked(m.card()).equals(m));

        System.out.println("NaN record equals:  " + new Rate(Double.NaN).equals(new Rate(Double.NaN))
                + "  (but NaN == NaN is " + (Double.NaN == Double.NaN) + ")");
        System.out.println("0.0 vs -0.0 equals: " + new Rate(0.0).equals(new Rate(-0.0))
                + " (but 0.0 == -0.0 is " + (0.0 == -0.0) + ")");
    }
}
