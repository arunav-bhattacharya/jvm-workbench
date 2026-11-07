package pay.card;

public record Card(String network, String last4) implements pay.api.PaymentMethod {}
