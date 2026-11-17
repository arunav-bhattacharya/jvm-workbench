package workbench.reactive.l08;

/** Something that happened to a cake order: "placed", "baked", "collected". */
public record OrderEvent(String orderId, String type) {
}
