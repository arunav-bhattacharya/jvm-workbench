package workbench.patterns.l05;

@FunctionalInterface
public interface FeeCalculator {

    record Payment(long amountMinor, String country) {}

    long feeMinor(Payment p);

    static FeeCalculator percent(int bps) {
        return p -> p.amountMinor() * bps / 10_000;
    }

    // each decorator is a lambda that calls the calculator it wraps (this::feeMinor) and adds one rule
    default FeeCalculator plusFixed(long fixedMinor) {
        return p -> feeMinor(p) + fixedMinor;
    }

    default FeeCalculator crossBorder(String home, int extraBps) {
        return p -> feeMinor(p) + (p.country().equals(home) ? 0 : p.amountMinor() * extraBps / 10_000);
    }

    default FeeCalculator cappedAt(long capMinor) {
        return p -> Math.min(feeMinor(p), capMinor);
    }
}
