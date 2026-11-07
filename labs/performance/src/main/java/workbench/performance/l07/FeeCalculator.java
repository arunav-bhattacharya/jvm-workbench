package workbench.performance.l07;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.regex.Pattern;

/**
 * The card fee for one payment: 2.9% of the amount plus 0.30, rounded half-even to cents.
 * It is correct. Under load it allocates about 2 KB per call, and the GC pauses show up in p99.99.
 *
 * <p>Your job: keep the results, the exception and the DEBUG message exactly as they are, and get
 * allocation under 100 bytes per call. Profile first (FeeInvestigation), fix one thing, measure again.
 */
public final class FeeCalculator {
    private final DebugLog log;

    public FeeCalculator(DebugLog log) {
        this.log = log;
    }

    /** Fee in cents. Throws IllegalArgumentException("bad currency") unless the currency is 3 letters A to Z. */
    public long feeCents(Payment p) {
        if (!Pattern.compile("^[A-Z]{3}$").matcher(p.currency()).matches())
            throw new IllegalArgumentException("bad currency");
        BigDecimal amount = new BigDecimal(p.amount());
        BigDecimal fee = amount.multiply(new BigDecimal("0.029")).add(new BigDecimal("0.30"))
                .setScale(2, RoundingMode.HALF_EVEN);
        log.debug(String.format("payment %s merchant=%s amount=%s fee=%s",   // dropped by the log when DEBUG is off
                p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
        return fee.unscaledValue().longValue();
    }
}
