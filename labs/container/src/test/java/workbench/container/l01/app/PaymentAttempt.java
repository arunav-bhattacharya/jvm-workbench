package workbench.container.l01.app;

import workbench.container.l01.Component;
import workbench.container.l01.Scope;

/** One attempt to pay: a fresh object per use, so it is a prototype. */
@Component(scope = Scope.PROTOTYPE)
public class PaymentAttempt {
    private final FeeCalculator fees;

    public PaymentAttempt(FeeCalculator fees) {
        this.fees = fees;
    }

    public FeeCalculator fees() {
        return fees;
    }
}
