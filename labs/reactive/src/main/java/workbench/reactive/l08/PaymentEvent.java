package workbench.reactive.l08;

/** Something that happened to a payment: "authorized", "captured", "refunded". */
public record PaymentEvent(String paymentId, String type) {
}
