package workbench.startup.l03;

/** The card issuer's API, as a REST client library would declare it. Don't change this interface. */
public interface CardIssuerClient {
    String authorize(String paymentId);
}
