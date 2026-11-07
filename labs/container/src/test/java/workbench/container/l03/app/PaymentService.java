package workbench.container.l03.app;

import workbench.container.l03.Component;

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

    public CardIssuerClient issuer() { return issuer; }
    public FeeCalculator fees() { return fees; }
    public Ledger ledger() { return ledger; }

    public String pay(String pan, long amountMinor) {
        String auth = issuer.authorize(pan, amountMinor);
        ledger.post(auth + " fee=" + fees.feeMinor(amountMinor));
        return auth;
    }
}
