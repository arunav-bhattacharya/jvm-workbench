package workbench.reactive.l02;

/** A blocking client for the card issuer. Each call is a network round trip that costs real money. */
public interface IssuerApi {
    /** Returns the payment's status, such as "SETTLED", or null if the issuer doesn't know the payment. */
    String fetchStatus(String paymentId);
}
