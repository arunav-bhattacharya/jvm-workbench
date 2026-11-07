package workbench.startup.l04.demo;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Runs the same work in 10 rounds in a fresh JVM and prints how long each round took. A fresh
 * JVM starts in the interpreter, then the JIT compiles the hot code. Extra arguments are passed
 * to that JVM as flags, for example -Xint (interpreter only) or -XX:TieredStopAtLevel=1 (C1 only).
 */
public class WarmupDemo {
    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--work")) {
            work();
            return;
        }
        List<String> cmd = new ArrayList<>();
        cmd.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        cmd.addAll(List.of(args));
        cmd.addAll(List.of("-cp", System.getProperty("java.class.path"), WarmupDemo.class.getName(), "--work"));
        System.out.println("fresh JVM, flags " + List.of(args));
        Process child = new ProcessBuilder(cmd).redirectErrorStream(true).inheritIO().start();
        child.waitFor();
    }

    /** Ten rounds of 20,000 Luhn checks on card numbers, the check every PAN field gets. */
    static void work() {
        long checksum = 0;
        for (int round = 1; round <= 10; round++) {
            long t0 = System.nanoTime();
            for (int i = 0; i < 20_000; i++) {
                String digits = Long.toString(1_000_003L * i + round);
                String pan = "4000" + "0".repeat(12 - digits.length()) + digits;   // a 16-digit PAN
                if (luhnValid(pan)) checksum += i;
            }
            long us = (System.nanoTime() - t0) / 1_000;
            System.out.printf("round %2d: %,7d us%n", round, us);
        }
        if (checksum == 42) System.out.println();   // keeps the JIT from dropping the work
    }

    static boolean luhnValid(String pan) {
        int sum = 0;
        boolean twice = false;
        for (int i = pan.length() - 1; i >= 0; i--) {
            int d = pan.charAt(i) - '0';
            if (twice) {
                d *= 2;
                if (d > 9) d -= 9;
            }
            sum += d;
            twice = !twice;
        }
        return sum % 10 == 0;
    }
}
