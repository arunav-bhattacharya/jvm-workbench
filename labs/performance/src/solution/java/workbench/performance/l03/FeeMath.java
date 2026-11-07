package workbench.performance.l03;

/** The code under test in this lab's benchmarks. Same file in src/main and src/solution. */
public final class FeeMath {
    private FeeMath() { }

    /** 2.9% + 30 cents, rounded half up, in cents. */
    public static long feeCents(long amountCents) {
        return (amountCents * 29 + 500) / 1000 + 30;
    }

    /** 19% tax on an amount, in cents, rounded down. */
    public static long taxCents(long amountCents) {
        return amountCents * 19 / 100;
    }
}
