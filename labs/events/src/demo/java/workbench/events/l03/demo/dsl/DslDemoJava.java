package workbench.events.l03.demo.dsl;

import kotlin.Unit;

/** The same wiring as DslDemo.kt, written in Java against the Kotlin DSL in that file. */
public class DslDemoJava {
    public static void main(String[] args) {
        Bus bus = new Bus();
        Timings timings = new Timings();
        Subscription handle = JavaDsl.subscriptions(bus, timings, b -> {                  // a Consumer: void lambda
            b.on(ParcelEvent.class, e -> System.out.println("tracking " + e.getParcelId() + " " + e.getClass().getSimpleName()));
            b.timed("load", g -> {                                                       // a Function1: the price of a
                g.on(ParcelCollected.class, c -> System.out.println("load     +" + c.getGrams() + " g"));   // receiver lambda
                g.on(ParcelDelivered.class, d -> System.out.println("load     -" + d.getGrams() + " g"));
                return Unit.INSTANCE;
            });
        });
        bus.publish(new ParcelCollected("PP-7781", 2_500));
        bus.publish(new ParcelDelivered("PP-7781", 2_500));
        bus.publish(new ParcelBooked("PP-7782", 1_200));
        System.out.println("load: " + timings.getCalls().get("load") + " calls, " + timings.getMillis().get("load")
                + " ms; handlers: " + bus.handlerCount());

        handle.close();                                                                  // close() throws nothing
        System.out.println("after close: " + bus.handlerCount() + " handlers");

        try {
            JavaDsl.subscriptions(bus, timings, b -> {
                b.on(ParcelCollected.class, c -> System.out.println("never subscribed"));
                throw new IllegalStateException("missing configuration: load limit");
            });
        } catch (IllegalStateException e) {
            System.out.println("block failed (" + e.getMessage() + "); handlers: " + bus.handlerCount());
        }
    }
}
