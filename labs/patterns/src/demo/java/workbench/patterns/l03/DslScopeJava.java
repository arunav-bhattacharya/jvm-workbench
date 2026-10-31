package workbench.patterns.l03;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * The Java twin of DslScope.kt. Java has no lambdas with receivers, so each block is a Consumer
 * that gets its builder as a named parameter (the style Spring Security uses for its config DSL).
 */
public class DslScopeJava {
    record Refund(String paymentId, long amountMinor) {}
    record RefundBatch(String reason, List<Refund> refunds) {}

    static final class RefundsBuilder {
        private final List<Refund> refunds = new ArrayList<>();
        RefundsBuilder refund(String paymentId, long amountMinor) { refunds.add(new Refund(paymentId, amountMinor)); return this; }
        List<Refund> build() { return List.copyOf(refunds); }
    }

    static final class RefundBatchBuilder {
        private String reason = "unspecified";
        private List<Refund> refunds = List.of();
        RefundBatchBuilder reason(String r) { reason = r; return this; }
        RefundBatchBuilder refunds(Consumer<RefundsBuilder> block) {
            RefundsBuilder b = new RefundsBuilder();
            block.accept(b);
            refunds = b.build();
            return this;
        }
        RefundBatch build() { return new RefundBatch(reason, refunds); }
    }

    static RefundBatch refundBatch(Consumer<RefundBatchBuilder> block) {
        RefundBatchBuilder b = new RefundBatchBuilder();
        block.accept(b);
        return b.build();
    }

    public static void main(String[] args) {
        RefundBatch batch = refundBatch(batchB -> {
            batchB.reason("duplicate charge");
            batchB.refunds(r -> {
                r.refund("p-101", 1_250);
                r.refund("p-102", 990);
                // batchB.reason("oops");   // step 2 of the Try it: this compiles, but you have to name batchB
            });
        });
        System.out.println(batch);
        System.out.println("total refunded: " + batch.refunds().stream().mapToLong(Refund::amountMinor).sum());
    }
}
