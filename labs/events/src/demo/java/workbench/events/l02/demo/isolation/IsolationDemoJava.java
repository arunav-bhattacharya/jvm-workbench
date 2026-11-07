package workbench.events.l02.demo.isolation;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

public class IsolationDemoJava {
    sealed interface PaymentEvent permits PaymentCaptured { String paymentId(); }
    record PaymentCaptured(String paymentId, long cents) implements PaymentEvent {}

    /** A list of handlers, stored in the list you pass; publish can isolate failures or not. */
    static final class Bus {
        private final List<Consumer<PaymentEvent>> handlers;
        private final boolean isolate;

        Bus(List<Consumer<PaymentEvent>> handlers, boolean isolate) { this.handlers = handlers; this.isolate = isolate; }

        AutoCloseable subscribe(Consumer<PaymentEvent> handler) {
            handlers.add(handler);
            return () -> handlers.remove(handler);
        }

        void publish(PaymentEvent event) {
            for (Consumer<PaymentEvent> h : handlers) {
                if (!isolate) { h.accept(event); continue; }
                try {
                    h.accept(event);
                } catch (RuntimeException e) {
                    System.out.println("  (error handler: " + e.getMessage() + ")");
                }
            }
        }
    }

    static void scenario(String title, Bus bus) {
        System.out.println(title);
        AtomicReference<AutoCloseable> once = new AtomicReference<>();
        once.set(bus.subscribe(e -> {                                   // unsubscribes itself
            System.out.println("  welcome email, once");
            try { once.get().close(); } catch (Exception x) { throw new IllegalStateException(x); }
        }));
        bus.subscribe(e -> { throw new IllegalStateException("ledger is down"); });
        bus.subscribe(e -> System.out.println("  receipt for " + e.paymentId()));
        try {
            bus.publish(new PaymentCaptured("pay_7781", 1_999));
            bus.publish(new PaymentCaptured("pay_7782", 250));
        } catch (RuntimeException e) {
            System.out.println("  publish threw " + e);
        }
    }

    public static void main(String[] args) {
        scenario("ArrayList, no isolation:", new Bus(new ArrayList<>(), false));
        scenario("CopyOnWriteArrayList, no isolation:", new Bus(new CopyOnWriteArrayList<>(), false));
        scenario("CopyOnWriteArrayList, isolated:", new Bus(new CopyOnWriteArrayList<>(), true));
    }
}
