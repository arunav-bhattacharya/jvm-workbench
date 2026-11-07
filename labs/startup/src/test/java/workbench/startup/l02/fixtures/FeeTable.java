package workbench.startup.l02.fixtures;

/** Its static initializer touches FeeRules, so initializing FeeTable loads FeeRules too. */
public final class FeeTable {
    static final int[] BASIS_POINTS = FeeRules.load();

    private FeeTable() {
    }

    public static long feeFor(long amountMinor) {
        return amountMinor * BASIS_POINTS[0] / 10_000;
    }
}
