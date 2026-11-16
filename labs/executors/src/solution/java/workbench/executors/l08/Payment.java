package workbench.executors.l08;

/** One card payment: an id such as "pay-7" and the amount in cents. */
public record Payment(String id, long amountCents) {}
