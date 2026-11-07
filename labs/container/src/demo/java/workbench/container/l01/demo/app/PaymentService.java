package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class PaymentService {
    private final CardIssuerClient issuer;
    private final FeeCalculator fees;
    private final Ledger ledger;

    public PaymentService(CardIssuerClient issuer, FeeCalculator fees, Ledger ledger) {
        this.issuer = issuer;
        this.fees = fees;
        this.ledger = ledger;
    }

    public void pay(String pan, long amountMinor) {
        ledger.post(issuer.authorize(pan, amountMinor) + " fee=" + fees.feeMinor(amountMinor));
    }
}
