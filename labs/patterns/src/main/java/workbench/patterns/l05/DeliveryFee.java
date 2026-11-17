package workbench.patterns.l05;

/**
 * The price of delivering one parcel, built from small decorators. Each default method returns a NEW
 * fee that wraps this one and adds one rule, so you can chain them:
 *
 * <pre>{@code
 * DeliveryFee fee = DeliveryFee.perKm(50).plusFixed(200).heavySurcharge(5_000, 300).cappedAt(800);
 * fee.cents(new Delivery(4, 2_000));   // 400: 2.00 to start, plus 4 km at 0.50
 * }</pre>
 *
 * All prices are in cents: 200 means 2.00.
 */
@FunctionalInterface
public interface DeliveryFee {

    /** One delivery: how far the parcel goes, and how much it weighs. */
    record Delivery(int km, int grams) {}

    long cents(Delivery d);

    /** The base rule: {@code centsPerKm} for every kilometer. */
    static DeliveryFee perKm(long centsPerKm) {
        throw new UnsupportedOperationException("TODO: return a lambda that charges centsPerKm for every km");
    }

    /** Adds a fixed charge on top of whatever this fee says. */
    default DeliveryFee plusFixed(long fixedCents) {
        throw new UnsupportedOperationException("TODO: wrap this fee and add the fixed charge");
    }

    /** Adds {@code extraCents} when the parcel weighs more than {@code overGrams}. */
    default DeliveryFee heavySurcharge(int overGrams, long extraCents) {
        throw new UnsupportedOperationException("TODO: wrap this fee and add the surcharge for heavy parcels");
    }

    /** Never charges more than {@code maxCents}, whatever this fee says. */
    default DeliveryFee cappedAt(long maxCents) {
        throw new UnsupportedOperationException("TODO: wrap this fee and cap its result");
    }
}
