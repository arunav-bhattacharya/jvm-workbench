package workbench.performance.l02;

import java.util.ArrayList;
import java.util.List;

/**
 * Settles batches of payments in three phases: card charges only, then a refund appears,
 * then SEPA and wallet payments appear. Run it: a second JVM starts with -XX:+PrintCompilation
 * and -Xlog:deoptimization=debug, and the demo prints what happened to settle().
 */
public class DeoptDemo {
    interface PaymentMethod { long feeCents(long amountCents); }
    record Card(long bps) implements PaymentMethod { public long feeCents(long a) { return a * bps / 10_000; } }
    record Sepa(long flat) implements PaymentMethod { public long feeCents(long a) { return flat; } }
    record Wallet(long bps, long flat) implements PaymentMethod { public long feeCents(long a) { return a * bps / 10_000 + flat; } }

    static long settle(PaymentMethod[] methods, long[] amounts, boolean[] refund) {
        long net = 0;
        for (int i = 0; i < amounts.length; i++) {
            long fee = methods[i].feeCents(amounts[i]);   // call site: which types has it seen?
            if (refund[i]) net -= amounts[i];             // branch: has it ever been taken?
            else net += amounts[i] - fee;
        }
        return net;
    }

    static void work() {
        int n = 1_000;
        PaymentMethod[] methods = new PaymentMethod[n];
        long[] amounts = new long[n];
        boolean[] refund = new boolean[n];
        for (int i = 0; i < n; i++) { methods[i] = new Card(290); amounts[i] = 1_000 + i; }
        long total = 0;

        System.out.println("phase 1: card charges only");
        for (int r = 0; r < 3_000; r++) total += settle(methods, amounts, refund);

        System.out.println("phase 2: one refund per batch");
        refund[500] = true;
        for (int r = 0; r < 3_000; r++) total += settle(methods, amounts, refund);

        System.out.println("phase 3: SEPA and wallet payments arrive");
        for (int i = 0; i < n; i += 3) methods[i] = new Sepa(35);
        for (int i = 1; i < n; i += 3) methods[i] = new Wallet(150, 10);
        for (int r = 0; r < 3_000; r++) total += settle(methods, amounts, refund);
        System.out.println("done, checksum " + total);
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { work(); return; }
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java, "-XX:+PrintCompilation", "-Xlog:deoptimization=debug",
                "-cp", System.getProperty("java.class.path"), DeoptDemo.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        try (var out = p.inputReader()) {
            out.lines()
               .filter(l -> l.contains("DeoptDemo::settle") || l.contains("DeoptDemo.settle") || l.startsWith("phase") || l.startsWith("done"))
               .map(l -> l.replaceAll(" pc=.*", ""))            // drop machine addresses
               .forEach(System.out::println);
        }
        p.waitFor();
    }
}
