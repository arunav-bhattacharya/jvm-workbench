package workbench.events.l03.demo.dsl;

import kotlin.Unit;

/** Java has no implicit receivers: reaching the outer builder takes an explicit b. that a reviewer sees. */
public class MarkerDemoJava {
    public static void main(String[] args) {
        Bus bus = new Bus();
        Timings timings = new Timings();
        JavaDsl.subscriptions(bus, timings, b -> {
            b.timed("ledger", g -> {
                g.on(PaymentCaptured.class, c -> System.out.println("ledger  +" + c.getCents()));
                // Step 2 (Java): this is the same mistake, and it has to be written out: b.timed, not g.timed.
                b.timed("refunds", r -> {
                    r.on(PaymentRefunded.class, e -> System.out.println("ledger  -" + e.getCents()));
                    return Unit.INSTANCE;
                });
                return Unit.INSTANCE;
            });
        });
        bus.publish(new PaymentCaptured("pay_7781", 1_999));
        bus.publish(new PaymentRefunded("pay_7781", 500));
        System.out.println("timed groups: " + timings.getCalls());
    }
}
