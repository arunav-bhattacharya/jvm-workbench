package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class PaymentService {
    private final CardIssuerClient issuer;
    private final FeeCalculator fees;
    private final RiskRules risk;
    private final Ledger ledger;

    public PaymentService(CardIssuerClient issuer, FeeCalculator fees, RiskRules risk, Ledger ledger) {
        this.issuer = issuer;
        this.fees = fees;
        this.risk = risk;
        this.ledger = ledger;
    }

    public String pay(String merchantId, String pan, long amountMinor) {
        if (!risk.allow(merchantId, amountMinor)) return "declined";
        String auth = issuer.authorize(pan, amountMinor);
        ledger.post(auth + " fee=" + fees.feeMinor(amountMinor));
        return auth;
    }
}
