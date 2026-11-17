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
    static long totalWords(long[] words) {
        long sum = 0;
        for (long w : words) sum = Math.addExact(sum, w);    // throws on overflow instead of wrapping
        return sum;
    }

    static boolean sameText(byte[] a, byte[] b) {
        return Arrays.equals(a, b);                          // compares many bytes per step
    }

    static int stylesOn(long styleBits) {
        return Long.bitCount(styleBits);                     // one POPCNT instruction on x86
    }

    static void work() {
        long[] words = new long[1_000];                      // the word counts of 1,000 documents
        Arrays.fill(words, 1_999);
        byte[] t1 = new byte[64], t2 = new byte[64];         // two texts, as bytes
        long s = 0;
        for (int i = 0; i < 200_000; i++) {
            s += totalWords(words);
            if (sameText(t1, t2)) s++;
            s += stylesOn(i);                                // bold, italic, ...: one bit per style
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
