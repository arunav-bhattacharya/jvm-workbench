package workbench.patterns.l07;

/** A parcel to price: how it travels, what it weighs, and which part of town it goes to. Given; don't change it. */
public record Parcel(DeliveryMethod method, int grams, String district) {}
