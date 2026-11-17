package workbench.performance.l01;

import java.util.ArrayList;
import java.util.List;

/**
 * Times the same batch of 20,000 reading-time calculations 12 times in a row.
 * No argument: normal tiered JVM. "int": interpreter only (-Xint). "c1": stop at C1 (-XX:TieredStopAtLevel=1).
 */
public class WarmupDemo {
    static final long[] WORDS = new long[20_000];   // the word counts of 20,000 documents

    // seconds to read a document at 238 words a minute, rounded up
    static long readingSeconds(long words) {
        return (words * 60 + 237) / 238;
    }

    static long batch() {
        long total = 0;
        for (long w : WORDS) total += readingSeconds(w);
        return total;
    }

    public static void main(String[] args) throws Exception {
        String mode = args.length > 0 ? args[0] : "tiered";
        if (mode.equals("int")) { relaunch("-Xint"); return; }
        if (mode.equals("c1")) { relaunch("-XX:TieredStopAtLevel=1"); return; }

        for (int i = 0; i < WORDS.length; i++) WORDS[i] = 50 + (i * 7919L) % 25_000;
        long check = 0;
        for (int round = 1; round <= 12; round++) {
            long t0 = System.nanoTime();
            check += batch();
            long micros = (System.nanoTime() - t0) / 1_000;
            System.out.printf("batch %2d: %,6d us%n", round, micros);
        }
        System.out.println("(checksum " + check + ")");   // use the result, so the JIT can't drop the work
    }

    // start a second JVM with extra flags and the same classpath, and show its output
    static void relaunch(String flag) throws Exception {
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java, flag, "-cp", System.getProperty("java.class.path"),
                WarmupDemo.class.getName(), "tiered"));
        System.out.println("running with " + flag);
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        try (var out = p.inputReader()) {
            out.lines().filter(l -> !l.startsWith("Picked up")).forEach(System.out::println);
        }
        p.waitFor();
    }
}
