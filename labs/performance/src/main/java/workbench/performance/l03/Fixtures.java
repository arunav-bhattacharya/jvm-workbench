package workbench.performance.l03;

import java.util.concurrent.atomic.AtomicInteger;

/** Test data for the benchmarks. Same file in src/main and src/solution. */
public final class Fixtures {
    /** How many batches have been built. The tests read it; benchmarks don't need to. */
    public static final AtomicInteger BUILDS = new AtomicInteger();

    private Fixtures() { }

    /** Writes out {@code n} made-up documents and counts their words, the slow way. Deliberately not cheap. */
    public static long[] batch(int n) {
        BUILDS.incrementAndGet();
        long[] words = new long[n];
        for (int i = 0; i < n; i++) {
            String text = "word ".repeat(1 + i % 300);   // a made-up document of 1 to 300 words
            words[i] = text.split(" ").length;
        }
        return words;
    }
}
