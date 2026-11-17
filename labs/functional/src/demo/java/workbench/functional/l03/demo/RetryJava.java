package workbench.functional.l03.demo;

import java.util.function.Supplier;

/**
 * Java twin of Retry.kt. The work comes in as a Supplier<T>. Supplier.get() can't throw checked
 * exceptions, so code that throws IOException needs Callable<T> and a `throws Exception` on retry.
 */
public class RetryJava {

    // A fake recipe website that times out a few times, then answers.
    static final class FlakySite {
        private int failuresLeft;
        int calls = 0;
        FlakySite(int failuresLeft) { this.failuresLeft = failuresLeft; }

        String fetch(String recipe) {
            calls++;
            if (failuresLeft-- > 0) throw new IllegalStateException("site timeout on call " + calls);
            return "page:" + recipe;
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
        FlakySite site = new FlakySite(2);
        String page = timed("fetch with retry", () -> retry(3, () -> site.fetch("pancakes")));
        System.out.println("result: " + page + " after " + site.calls + " calls");

        FlakySite down = new FlakySite(5);
        try {
            retry(3, () -> down.fetch("waffles"));
        } catch (IllegalStateException e) {
            System.out.println("result: " + e.getMessage() + " (last cause: " + e.getCause().getMessage() + ")");
        }
    }
}
