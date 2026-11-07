package workbench.performance.l07;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.regex.Pattern;

/** The fee calculation before and after each round of the investigation. Same results, different costs. */
public final class FeeVariants {
    record Payment(String id, String currency, String amount, String merchant) { }

    static volatile boolean debugEnabled = false;          // DEBUG is off, as in production

    static void debug(String message) {
        if (debugEnabled) System.out.println(message);
    }

    // before: a regex compiled per call, constants built per call, a log line formatted and dropped
    static long feeSlow(Payment p) {
        if (!Pattern.compile("^[A-Z]{3}$").matcher(p.currency()).matches())
            throw new IllegalArgumentException("bad currency");
        BigDecimal amount = new BigDecimal(p.amount());
        BigDecimal fee = amount.multiply(new BigDecimal("0.029")).add(new BigDecimal("0.30"))
                .setScale(2, RoundingMode.HALF_EVEN);
        debug(String.format("payment %s merchant=%s amount=%s fee=%s",
                p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
        return fee.unscaledValue().longValue();
    }

    // round 1: hoist the pattern and the constants, guard the log line
    static final Pattern CCY = Pattern.compile("^[A-Z]{3}$");
    static final BigDecimal RATE = new BigDecimal("0.029");
    static final BigDecimal FIXED = new BigDecimal("0.30");

    static long feeHoisted(Payment p) {
        if (!CCY.matcher(p.currency()).matches()) throw new IllegalArgumentException("bad currency");
        BigDecimal amount = new BigDecimal(p.amount());
        BigDecimal fee = amount.multiply(RATE).add(FIXED).setScale(2, RoundingMode.HALF_EVEN);
        if (debugEnabled) debug(String.format("payment %s merchant=%s amount=%s fee=%s",
                p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
        return fee.unscaledValue().longValue();
    }

    // round 2: the second profile pointed at Matcher; three letters don't need a regex
    static boolean isCurrencyCode(String s) {
        if (s.length() != 3) return false;
        for (int i = 0; i < 3; i++) {
            char c = s.charAt(i);
            if (c < 'A' || c > 'Z') return false;
        }
        return true;
    }

    static long feeNoRegex(Payment p) {
        if (!isCurrencyCode(p.currency())) throw new IllegalArgumentException("bad currency");
        BigDecimal amount = new BigDecimal(p.amount());
        BigDecimal fee = amount.multiply(RATE).add(FIXED).setScale(2, RoundingMode.HALF_EVEN);
        if (debugEnabled) debug(String.format("payment %s merchant=%s amount=%s fee=%s",
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

    private FeeVariants() { }
}
