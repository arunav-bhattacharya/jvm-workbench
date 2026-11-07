package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class RiskRules {
    private final MerchantDirectory merchants;

    public RiskRules(MerchantDirectory merchants) { this.merchants = merchants; }

    public boolean allow(String merchantId, long amountMinor) {
        return !merchants.categoryOf(merchantId).equals("5814") || amountMinor < 50_000;
    }
}
