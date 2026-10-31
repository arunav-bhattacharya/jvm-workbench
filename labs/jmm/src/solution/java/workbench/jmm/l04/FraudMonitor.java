package workbench.jmm.l04;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

public class FraudMonitor implements Consumer<PaymentEvent> {
    private final long limitCents;
    private final List<String> flagged;

    // the constructor only sets fields; it never hands `this` to anyone
    private FraudMonitor(long limitCents) {
        this.limitCents = limitCents;
        this.flagged = new CopyOnWriteArrayList<>();
    }

    public static FraudMonitor create(EventBus bus, long limitCents) {
        FraudMonitor m = new FraudMonitor(limitCents);   // 1. finish construction
        bus.register(m);                                 // 2. only then let other code see it
        return m;
    }

    @Override
    public void accept(PaymentEvent e) {
        if (e.amountCents() > limitCents) flagged.add(e.paymentId());
    }

    public List<String> flagged() {
        return List.copyOf(flagged);
    }
}
