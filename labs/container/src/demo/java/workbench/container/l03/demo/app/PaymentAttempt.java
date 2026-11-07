package workbench.container.l03.demo.app;

import workbench.container.l03.Component;
import workbench.container.l03.Scope;

@Component(scope = Scope.PROTOTYPE)
public class PaymentAttempt {
    private final FeeCalculator fees;

    public PaymentAttempt(FeeCalculator fees) { this.fees = fees; }

    public long feeMinor(long amountMinor) { return fees.feeMinor(amountMinor); }
}
