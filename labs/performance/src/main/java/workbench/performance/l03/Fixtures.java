package workbench.performance.l03;

import java.math.BigDecimal;
import java.util.concurrent.atomic.AtomicInteger;

/** Test data for the benchmarks. Same file in src/main and src/solution. */
public final class Fixtures {
    /** How many batches have been built. The tests read it; benchmarks don't need to. */
    public static final AtomicInteger BUILDS = new AtomicInteger();

    private Fixtures() { }

    /** Parses {@code n} amounts such as "19.99" into cents. Deliberately not cheap. */
    public static long[] batch(int n) {
        BUILDS.incrementAndGet();
        long[] cents = new long[n];
        for (int i = 0; i < n; i++) {
            String amount = (10 + i % 990) + "." + (10 + i % 89);
            cents[i] = new BigDecimal(amount).movePointRight(2).longValueExact();
        }
        return cents;
    }
}
