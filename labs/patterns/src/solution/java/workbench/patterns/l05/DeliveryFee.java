package workbench.patterns.l05;

@FunctionalInterface
public interface DeliveryFee {

    record Delivery(int km, int grams) {}

    long cents(Delivery d);

    static DeliveryFee perKm(long centsPerKm) {
        return d -> d.km() * centsPerKm;
    }

    // each decorator is a lambda that calls the fee it wraps (this.cents) and adds one rule
    default DeliveryFee plusFixed(long fixedCents) {
        return d -> cents(d) + fixedCents;
    }

    default DeliveryFee heavySurcharge(int overGrams, long extraCents) {
        return d -> cents(d) + (d.grams() > overGrams ? extraCents : 0);
    }

    default DeliveryFee cappedAt(long maxCents) {
        return d -> Math.min(cents(d), maxCents);
    }
}
