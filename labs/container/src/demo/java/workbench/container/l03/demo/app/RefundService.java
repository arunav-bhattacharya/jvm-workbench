package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class RefundService {
    private final CardIssuerClient issuer;
    private final Ledger ledger;

    public RefundService(CardIssuerClient issuer, Ledger ledger) {
        this.issuer = issuer;
        this.ledger = ledger;
    }

    public String refund(String authId, long amountMinor) {
        String ref = issuer.refund(authId, amountMinor);
        ledger.post(ref);
        return ref;
    }
}
