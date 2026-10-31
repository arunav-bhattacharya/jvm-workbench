package workbench.jmm.l04;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/**
 * Flags payments above a limit. It listens on an {@link EventBus}.
 *
 * <p>The bug: the constructor registers {@code this} on the bus before it has set its fields.
 * The bus replays its last event at once, so {@link #accept} runs on a half-built object.
 * Fix it so no other code can see the monitor before its constructor has finished.
 * Keep {@link #create} as the only way to make one.
 */
public class FraudMonitor implements Consumer<PaymentEvent> {
    private final long limitCents;
    private final List<String> flagged;

    private FraudMonitor(EventBus bus, long limitCents) {
        bus.register(this);                          // `this` escapes before the fields below are set
        this.limitCents = limitCents;
        this.flagged = new CopyOnWriteArrayList<>();
    }

    /** Creates a monitor and starts listening on {@code bus}. */
    public static FraudMonitor create(EventBus bus, long limitCents) {
        return new FraudMonitor(bus, limitCents);
    }

    @Override
    public void accept(PaymentEvent e) {
        if (e.amountCents() > limitCents) flagged.add(e.paymentId());
    }

    /** The ids of the payments flagged so far. */
    public List<String> flagged() {
        return List.copyOf(flagged);
    }
}
