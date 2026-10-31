package workbench.patterns.l05;

/**
 * A fee calculator, built from small decorators. Each default method returns a NEW calculator that
 * wraps this one and adds one rule, so you can chain them:
 *
 * <pre>{@code
 * FeeCalculator calc = FeeCalculator.percent(290).plusFixed(30).crossBorder("DE", 100).cappedAt(500);
 * calc.feeMinor(new Payment(10_000, "DE"));   // 320
 * }</pre>
 *
 * Amounts are in minor units (cents). Divide with integer division: 10,000 x 290 / 10,000 = 290.
 */
@FunctionalInterface
public interface FeeCalculator {

    record Payment(long amountMinor, String country) {}

    long feeMinor(Payment p);

    /** The base rule: {@code bps} basis points of the amount (290 bps = 2.9%). */
    static FeeCalculator percent(int bps) {
        throw new UnsupportedOperationException("TODO: return a lambda that takes bps of the amount");
    }

    /** Adds a fixed fee on top of whatever this calculator charges. */
    default FeeCalculator plusFixed(long fixedMinor) {
        throw new UnsupportedOperationException("TODO: wrap this calculator and add the fixed fee");
    }

    /** Adds {@code extraBps} of the amount when the payment's country is not {@code home}. */
    default FeeCalculator crossBorder(String home, int extraBps) {
        throw new UnsupportedOperationException("TODO: wrap this calculator and add the surcharge abroad");
    }

    /** Never charges more than {@code capMinor}, whatever this calculator says. */
    default FeeCalculator cappedAt(long capMinor) {
        throw new UnsupportedOperationException("TODO: wrap this calculator and cap its result");
    }
}
