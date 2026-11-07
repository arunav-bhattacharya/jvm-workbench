package workbench.performance.l06;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.regex.Pattern;

/** The fee calculation lessons 6 and 7 investigate. It is correct, and it hides three costs. */
public final class SlowFees {
    record Payment(String id, String currency, String amount, String merchant) { }

    static volatile boolean debugEnabled = false;          // DEBUG logging is off in production

    private SlowFees() { }

    static void debug(String message) {
        if (debugEnabled) System.out.println(message);
    }

    static long feeSlow(Payment p) {
        if (!Pattern.compile("^[A-Z]{3}$").matcher(p.currency()).matches())    // a regex compiled per call
            throw new IllegalArgumentException("bad currency");
        BigDecimal amount = new BigDecimal(p.amount());
        BigDecimal fee = amount.multiply(new BigDecimal("0.029")).add(new BigDecimal("0.30"))
                .setScale(2, RoundingMode.HALF_EVEN);
        debug(String.format("payment %s merchant=%s amount=%s fee=%s",           // formatted, then thrown away
                p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
        return fee.unscaledValue().longValue();
    }

    static Payment[] payments(int n) {
        Payment[] ps = new Payment[n];
        for (int i = 0; i < n; i++) {
            ps[i] = new Payment("pay_" + i, i % 2 == 0 ? "EUR" : "USD",
                    (1 + (i * 7_919) % 99_999) + "." + (10 + i % 89), "m_" + (i % 50));
        }
        return ps;
    }

    /** Runs feeSlow on {@code threads} threads until the deadline. */
    static void hammer(int threads, long untilNanos) throws InterruptedException {
        Payment[] ps = payments(4_096);
        Thread[] ts = new Thread[threads];
        for (int t = 0; t < threads; t++) {
            int seed = t;
            ts[t] = new Thread(() -> {
                long sink = 0;
                for (int i = seed; System.nanoTime() < untilNanos; i++) sink += feeSlow(ps[i & 4095]);
                if (sink == 42) System.out.println();
            }, "fees-" + t);
            ts[t].start();
        }
        for (Thread t : ts) t.join();
    }
}
