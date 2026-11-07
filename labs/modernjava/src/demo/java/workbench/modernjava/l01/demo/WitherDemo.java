package workbench.modernjava.l01.demo;

import java.util.List;

/** Java has no copy(): you write withers by hand, and each one calls the canonical constructor. */
public class WitherDemo {

    record Refund(String paymentId, long amountMinor, List<String> reasons) {
        Refund {
            if (amountMinor <= 0) throw new IllegalArgumentException("refund must be positive: " + amountMinor);
            reasons = List.copyOf(reasons);
        }

        Refund withAmount(long newAmount) { return new Refund(paymentId, newAmount, reasons); }
        Refund withReason(String extra) {
            var more = new java.util.ArrayList<>(reasons);
            more.add(extra);
            return new Refund(paymentId, amountMinor, more);
        }
    }

    public static void main(String[] args) {
        Refund full = new Refund("pay_81", 5_000, List.of("duplicate charge"));
        Refund part = full.withAmount(2_000).withReason("partial goodwill");

        System.out.println("original: " + full);
        System.out.println("changed:  " + part);
        System.out.println("same reasons list object: " + (full.reasons() == full.withAmount(1_000).reasons()));
        try {
            full.withAmount(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("wither ran the checks: " + e.getMessage());
        }
    }
}
