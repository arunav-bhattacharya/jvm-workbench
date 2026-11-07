package workbench.container.l03.demo.app;

import workbench.container.l03.Component;
import workbench.container.l03.SettlementService;

@Component
public class PayoutJob {
    private final SettlementService settlement;
    private final Ledger ledger;

    public PayoutJob(SettlementService settlement, Ledger ledger) {
        this.settlement = settlement;
        this.ledger = ledger;
    }

    public String run(String batch) {
        String result = settlement.settle(batch);
        ledger.post(result);
        return result;
    }
}
