package workbench.container.l01.demo.app;

public interface CardIssuerClient {
    String authorize(String pan, long amountMinor);
}
