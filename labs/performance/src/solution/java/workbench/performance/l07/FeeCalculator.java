package workbench.performance.l07;

import java.math.BigDecimal;
import java.math.RoundingMode;

public final class FeeCalculator {
    // round 1: constants are built once, not per call
    private static final BigDecimal RATE = new BigDecimal("0.029");
    private static final BigDecimal FIXED = new BigDecimal("0.30");

    private final DebugLog log;

    public FeeCalculator(DebugLog log) {
        this.log = log;
    }

    public long feeCents(Payment p) {
        if (!isCurrencyCode(p.currency())) throw new IllegalArgumentException("bad currency");
        BigDecimal amount = new BigDecimal(p.amount());              // what's left: about 72 bytes per call
        BigDecimal fee = amount.multiply(RATE).add(FIXED).setScale(2, RoundingMode.HALF_EVEN);
        if (log.isDebugEnabled()) {                                  // round 1: format only when someone reads it
            log.debug(String.format("payment %s merchant=%s amount=%s fee=%s",
                    p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
        }
        return fee.unscaledValue().longValue();
    }

    // round 2: the re-profile showed Matcher allocation next; three characters don't need a regex
    static boolean isCurrencyCode(String s) {
        if (s.length() != 3) return false;
        for (int i = 0; i < 3; i++) {
            char c = s.charAt(i);
            if (c < 'A' || c > 'Z') return false;
        }
        return true;
    }
}
