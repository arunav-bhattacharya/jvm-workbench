// Java equivalent: the same jitter formula with java.util.Random; the waits are computed, not slept
package workbench.quotes.l03;

import java.util.Map;
import java.util.Random;
import java.util.TreeMap;

/** 1,000 clients fail together at 0 ms and retry after a nominal 100 ms. When do the retries land? */
public class RetryJitterDemoJava {
    public static void main(String[] args) {
        for (double jitter : new double[] {0.0, 0.5}) {
            Random random = new Random(7);
            Map<Integer, Integer> buckets = new TreeMap<>();
            Map<Integer, Integer> perMs = new TreeMap<>();
            for (int client = 0; client < 1_000; client++) {
                double factor = 1 + jitter * (random.nextDouble() * 2 - 1);   // 1 - jitter .. 1 + jitter
                int at = (int) Math.ceil(100 * factor);                         // delay rounds up to whole ms
                buckets.merge(at / 25 * 25, 1, Integer::sum);
                perMs.merge(at, 1, Integer::sum);
            }
            StringBuilder line = new StringBuilder("jitter " + jitter + ":");
            buckets.forEach((from, hits) -> line.append(String.format("  %d-%d ms: %d", from, from + 24, hits)));
            System.out.println(line);
            System.out.println("   most retries in one millisecond: " + perMs.values().stream().mapToInt(Integer::intValue).max().orElse(0));
        }
    }
}
