package workbench.memory.l05;

import workbench.memory.Jvm;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Epsilon never frees anything, so a heap of 64 MB is an allocation budget. Two versions of the same
 * settlement totals run against that budget, each in its own child JVM.
 */
public class EpsilonDemo {
    static final int PAYMENTS = 5_000_000, MERCHANTS = 500;

    static long boxedTotals() {
        Map<Integer, Long> totals = new HashMap<>();
        // every sum is a new Long stored in the map: at least 24 bytes per payment, even when the JIT
        // removes the temporary boxes for the key and the amount
        for (int i = 0; i < PAYMENTS; i++) totals.merge(i % MERCHANTS, 1_000L + i % 9_000, Long::sum);
        return totals.values().stream().mapToLong(Long::longValue).sum();
    }

    static long primitiveTotals() {
        long[] totals = new long[MERCHANTS];
        for (int i = 0; i < PAYMENTS; i++) totals[i % MERCHANTS] += 1_000L + i % 9_000;                // no objects
        long sum = 0;
        for (long t : totals) sum += t;
        return sum;
    }

    public static void main(String[] args) {
        if (args.length > 0) {
            long sum = args[0].equals("boxed") ? boxedTotals() : primitiveTotals();
            System.out.println("finished inside the budget, total " + sum);
            return;
        }
        List<String> epsilon = List.of("-XX:+UnlockExperimentalVMOptions", "-XX:+UseEpsilonGC", "-Xmx64m");
        for (String version : List.of("primitive", "boxed")) {
            System.out.println("== " + version);
            Jvm.lines(epsilon, EpsilonDemo.class.getName(), version).forEach(System.out::println);
        }
    }
}
