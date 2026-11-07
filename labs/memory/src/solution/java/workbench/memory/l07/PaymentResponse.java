package workbench.memory.l07;

/** What the API answered. A retry with the same idempotency key must get this same answer. */
public record PaymentResponse(String paymentId, String status, long amountMinor) {}
