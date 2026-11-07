package workbench.performance.l02;

import java.util.ArrayList;
import java.util.List;

/**
 * Two versions of the same amount check. One builds its error message inline, the other moves
 * the cold path into a helper. Run it: a second JVM starts with -XX:+PrintInlining and the demo
 * prints what C1 and C2 decided at the two call sites in refund().
 */
public class InliningDemo {
    static final long MAX_CENTS = 100_000_000L;

    // the error message is built right here, so its bytecode counts against the inlining budget
    static long requireAmountInline(long cents) {
        if (cents <= 0 || cents > MAX_CENTS) {
            throw new IllegalArgumentException(
                    String.format("amount must be between 1 and %d cents, got %d", MAX_CENTS, cents));
        }
        return cents;
    }

    // same check, but the cold path lives in its own method
    static long requireAmountSplit(long cents) {
        if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents);
        return cents;
    }

    static IllegalArgumentException badAmount(long cents) {
        return new IllegalArgumentException(
                String.format("amount must be between 1 and %d cents, got %d", MAX_CENTS, cents));
    }

    // each check runs on 1 call in 8, so neither call site counts as hot for C2
    static long refund(long cents, int i) {
        long r = cents / 2;
        if ((i & 7) == 0) r += requireAmountInline(cents);
        if ((i & 7) == 1) r += requireAmountSplit(cents);
        return r;
    }

    static void work() {
        long s = 0;
        for (int i = 0; i < 2_000_000; i++) s += refund(1_000 + (i & 1023), i);
        System.out.println("checksum " + s);
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { work(); return; }
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java,
                "-XX:+UnlockDiagnosticVMOptions", "-XX:+PrintInlining", "-XX:+PrintCompilation",
                "-cp", System.getProperty("java.class.path"), InliningDemo.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        try (var out = p.inputReader()) {
            // keep the compile lines for refund() and the decisions about the two checks
            out.lines()
               .filter(l -> l.contains("InliningDemo::refund (") || l.contains("requireAmount") || l.startsWith("checksum"))
               .forEach(System.out::println);
        }
        p.waitFor();
    }
}
