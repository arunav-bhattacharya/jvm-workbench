package workbench.patterns.l07;

/** A payment to price. Amounts are in minor units (cents). Given; don't change it. */
public record Payment(Method method, long amountMinor, String country) {}
