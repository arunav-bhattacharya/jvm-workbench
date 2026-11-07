package workbench.patterns.l07;

/**
 * The fee logic as it runs in production today. It is ugly, and it is also the specification:
 * the tests check that your refactors give exactly the same answers. Given; don't change it.
 */
public final class LegacyRouter {
    private LegacyRouter() {}

    public static long fee(Payment p) {
        if (p.method() == Method.CARD) {
            long fee = 30 + p.amountMinor() * 290 / 10_000;
            if (!p.country().equals("DE")) {
                fee += p.amountMinor() * 100 / 10_000;          // cross-border cards pay 1% more
            }
            return fee;
        } else if (p.method() == Method.SEPA) {
            return 25;
        } else if (p.method() == Method.WALLET) {
            return p.amountMinor() * 150 / 10_000;
        } else {
            throw new IllegalArgumentException("unknown method " + p.method());
        }
    }
}
