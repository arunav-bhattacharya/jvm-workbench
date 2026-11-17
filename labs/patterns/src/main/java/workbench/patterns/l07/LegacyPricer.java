package workbench.patterns.l07;

/**
 * The delivery prices as the shop's program charges them today, in cents. It is ugly, and it is also
 * the specification: the tests check that your refactors give exactly the same answers. Given; don't change it.
 */
public final class LegacyPricer {
    private LegacyPricer() {}

    public static long priceCents(Parcel p) {
        if (p.method() == DeliveryMethod.BIKE) {
            long price = 200 + p.grams() * 30 / 1_000;
            if (!p.district().equals("Old Town")) {
                price += p.grams() * 10 / 1_000;          // the hills outside the Old Town: 0.10 more per kg
            }
            return price;
        } else if (p.method() == DeliveryMethod.VAN) {
            return 450;
        } else if (p.method() == DeliveryMethod.PICKUP) {
            return 0;
        } else {
            throw new IllegalArgumentException("unknown delivery method " + p.method());
        }
    }
}
