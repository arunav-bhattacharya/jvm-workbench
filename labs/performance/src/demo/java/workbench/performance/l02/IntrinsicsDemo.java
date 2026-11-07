package workbench.performance.l02;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.TreeSet;

/**
 * Calls three JDK methods that HotSpot replaces with hand-written machine code. Run it: a second
 * JVM starts with -XX:+PrintInlining and the demo lists the intrinsic decisions for them.
 */
public class IntrinsicsDemo {
    static long totalCents(long[] cents) {
        long sum = 0;
        for (long c : cents) sum = Math.addExact(sum, c);   // throws on overflow instead of wrapping
        return sum;
    }

    static boolean sameKey(byte[] a, byte[] b) {
        return Arrays.equals(a, b);                          // compares many bytes per step
    }

    static int riskFlags(long mask) {
        return Long.bitCount(mask);                          // one POPCNT instruction on x86
    }

    static void work() {
        long[] cents = new long[1_000];
        Arrays.fill(cents, 1_999);
        byte[] k1 = new byte[64], k2 = new byte[64];
        long s = 0;
        for (int i = 0; i < 200_000; i++) {
            s += totalCents(cents);
            if (sameKey(k1, k2)) s++;
            s += riskFlags(i);
        }
        System.out.println("checksum " + s);
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { work(); return; }
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java, "-XX:+UnlockDiagnosticVMOptions", "-XX:+PrintInlining",
                "-cp", System.getProperty("java.class.path"), IntrinsicsDemo.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        TreeSet<String> seen = new TreeSet<>();
        try (var out = p.inputReader()) {
            out.lines()
               .filter(l -> l.contains("intrinsic"))
               .filter(l -> l.contains("Math::addExact") || l.contains("Arrays::equals") || l.contains("Long::bitCount"))
               .map(l -> l.replaceFirst("^\\s*@ \\d+\\s+", ""))   // drop the indent and the call-site index
               .forEach(seen::add);
        }
        p.waitFor();
        seen.forEach(System.out::println);
    }
}
