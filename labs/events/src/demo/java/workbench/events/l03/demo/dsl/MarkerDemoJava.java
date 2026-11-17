package workbench.events.l03.demo.dsl;

import kotlin.Unit;

/** Java has no implicit receivers: reaching the outer builder takes an explicit b. that a reviewer sees. */
public class MarkerDemoJava {
    public static void main(String[] args) {
        Bus bus = new Bus();
        Timings timings = new Timings();
        JavaDsl.subscriptions(bus, timings, b -> {
            b.timed("load", g -> {
                g.on(ParcelCollected.class, c -> System.out.println("load     +" + c.getGrams() + " g"));
                // Step 2 (Java): this is the same mistake, and it has to be written out: b.timed, not g.timed.
                b.timed("deliveries", d -> {
                    d.on(ParcelDelivered.class, e -> System.out.println("load     -" + e.getGrams() + " g"));
                    return Unit.INSTANCE;
                });
                return Unit.INSTANCE;
            });
        });
        bus.publish(new ParcelCollected("PP-7781", 2_500));
        bus.publish(new ParcelDelivered("PP-7781", 2_500));
        System.out.println("timed groups: " + timings.getCalls());
    }
}
