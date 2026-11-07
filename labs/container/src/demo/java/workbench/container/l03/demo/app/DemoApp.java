package workbench.container.l03.demo.app;

import workbench.container.l03.Registry;
import workbench.container.l03.SettlementLedger;
import workbench.container.l03.SettlementService;

import java.util.List;

/** The capstone's payment app: 14 components, two of them intercepted (one by interface, one by subclass). */
public final class DemoApp {
    private DemoApp() {}

    public static final List<Class<?>> COMPONENTS = List.of(
            PaymentService.class, RefundService.class, PayoutJob.class, PaymentAttempt.class,
            HttpIssuerClient.class, IssuerConfig.class,
            FeeCalculator.class, FxRates.class, RiskRules.class, MerchantDirectory.class, Ledger.class,
            SettlementService.class, SettlementLedger.class, AuditClock.class);

    /** One payment, one refund, one payout: every component and both kinds of interception get used. */
    public static String run(Registry registry) {
        String auth = registry.get(PaymentService.class).pay("m_42", "4111111111111111", 12_000);
        String ref = registry.get(RefundService.class).refund(auth, 2_000);
        String payout = registry.get(PayoutJob.class).run("B-17");
        long fee = registry.get(PaymentAttempt.class).feeMinor(12_000);
        return auth + ", " + ref + ", " + payout + ", fee " + fee + ", ledger lines " + registry.get(Ledger.class).size();
    }
}
