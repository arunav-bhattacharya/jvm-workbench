package workbench.jmm.l04;

/** A payment seen on the event bus. Records have final fields, so this one is immutable. */
public record PaymentEvent(String paymentId, long amountCents) {}
