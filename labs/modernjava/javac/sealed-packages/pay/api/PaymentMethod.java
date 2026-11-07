package pay.api;

// The sealed interface lives in pay.api, its only permitted subtype in pay.card.
// Compile it without module-info.java and javac refuses; compile it with module-info.java and it works.
public sealed interface PaymentMethod permits pay.card.Card {}
