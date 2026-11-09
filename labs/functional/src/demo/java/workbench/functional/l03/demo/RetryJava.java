package workbench.functional.l03.demo;

import java.util.function.Supplier;

/**
 * Java twin of Retry.kt. The work comes in as a Supplier<T>. Supplier.get() can't throw checked
 * exceptions, so code that throws IOException needs Callable<T> and a `throws Exception` on retry.
 */
public class RetryJava {

    static final class FlakyIssuer {
        private int failuresLeft;
        int calls = 0;
        FlakyIssuer(int failuresLeft) { this.failuresLeft = failuresLeft; }

        String authorize(String paymentId) {
            calls++;
            if (failuresLeft-- > 0) throw new IllegalStateException("issuer timeout on call " + calls);
            return "auth_" + paymentId;
        }
    }

    // A higher-order method: the loop is written once, and the work comes in as a function.
    static <T> T retry(int times, Supplier<T> block) {
        RuntimeException last = null;
        for (int attempt = 1; attempt <= times; attempt++) {
            try {
                return block.get();
            } catch (RuntimeException e) {
                last = e;
                System.out.println("  attempt " + attempt + " failed: " + e.getMessage());
            }
        }
        throw new IllegalStateException("gave up after " + times + " attempts", last);
    }

    // Another one: run any block, report how long it took, hand back its result unchanged.
    static <T> T timed(String label, Supplier<T> block) {
        long start = System.nanoTime();
        try {
            return block.get();
        } finally {
            System.out.printf("  %s took %.2f ms%n", label, (System.nanoTime() - start) / 1e6);
        }
    }

    public static void main(String[] args) {
        FlakyIssuer issuer = new FlakyIssuer(2);
        String auth = timed("authorize with retry", () -> retry(3, () -> issuer.authorize("pay_42")));
        System.out.println("result: " + auth + " after " + issuer.calls + " calls");

        FlakyIssuer down = new FlakyIssuer(5);
        try {
            retry(3, () -> down.authorize("pay_43"));
        } catch (IllegalStateException e) {
            System.out.println("result: " + e.getMessage() + " (last cause: " + e.getCause().getMessage() + ")");
        }
    }
}
