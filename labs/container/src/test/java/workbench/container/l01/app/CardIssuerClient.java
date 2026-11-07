package workbench.container.l01.app;

public interface CardIssuerClient {
    String authorize(String pan, long amountMinor);
}
