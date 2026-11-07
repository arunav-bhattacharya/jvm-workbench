package workbench.memory.l07;

/** A payment request as the API received it. {@code rawBody} is the JSON body, a few kilobytes. */
public record PaymentRequest(String idempotencyKey, String merchantId, long amountMinor, byte[] rawBody) {}
