package workbench.events.l03.demo.dsl;

import kotlin.Unit;

/** The same wiring as DslDemo.kt, written in Java against the Kotlin DSL in that file. */
public class DslDemoJava {
    public static void main(String[] args) {
        Bus bus = new Bus();
        Timings timings = new Timings();
        Subscription handle = JavaDsl.subscriptions(bus, timings, b -> {                  // a Consumer: void lambda
            b.on(PaymentEvent.class, e -> System.out.println("audit   " + e.getPaymentId() + " " + e.getClass().getSimpleName()));
            b.timed("ledger", g -> {                                                     // a Function1: the price of a
                g.on(PaymentCaptured.class, c -> System.out.println("ledger  +" + c.getCents()));   // receiver lambda
                g.on(PaymentRefunded.class, r -> System.out.println("ledger  -" + r.getCents()));
                return Unit.INSTANCE;
            });
        });
        bus.publish(new PaymentCaptured("pay_7781", 1_999));
        bus.publish(new PaymentRefunded("pay_7781", 500));
        bus.publish(new PaymentAuthorized("pay_7782", 250));
        System.out.println("ledger: " + timings.getCalls().get("ledger") + " calls, " + timings.getMillis().get("ledger")
                + " ms; handlers: " + bus.handlerCount());

        handle.close();                                                                  // close() throws nothing
        System.out.println("after close: " + bus.handlerCount() + " handlers");

        try {
            JavaDsl.subscriptions(bus, timings, b -> {
                b.on(PaymentCaptured.class, c -> System.out.println("never subscribed"));
                throw new IllegalStateException("missing configuration: ledger account");
            });
        } catch (IllegalStateException e) {
            System.out.println("block failed (" + e.getMessage() + "); handlers: " + bus.handlerCount());
        }
    }
}
