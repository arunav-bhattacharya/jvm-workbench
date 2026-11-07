package workbench.events.l02.demo.variance;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class VarianceDemoJava {
    sealed interface PaymentEvent permits PaymentCaptured, PaymentRefunded { String paymentId(); }
    record PaymentCaptured(String paymentId, long cents) implements PaymentEvent {}
    record PaymentRefunded(String paymentId, long cents) implements PaymentEvent {}

    /** Java interfaces have no declaration-site variance: every use site says ? super. */
    @FunctionalInterface
    interface Handler<E extends PaymentEvent> {
        void handle(E event);
    }

    static final class Bus {
        private final List<Map.Entry<Class<?>, Handler<PaymentEvent>>> handlers = new ArrayList<>();

        // Step 2: change Handler<? super E> to Handler<E> and run again.
        <E extends PaymentEvent> void subscribe(Class<E> type, Handler<? super E> handler) {
            handlers.add(Map.entry(type, event -> handler.handle(type.cast(event))));
        }

        void publish(PaymentEvent event) {
            for (var entry : handlers) if (entry.getKey().isInstance(event)) entry.getValue().handle(event);
        }
    }

    public static void main(String[] args) throws Exception {
        Handler<PaymentEvent> audit = e -> System.out.println("audit   " + e.paymentId() + " (" + e.getClass().getSimpleName() + ")");
        Handler<PaymentCaptured> ledger = e -> System.out.println("ledger  +" + e.cents());

        Bus bus = new Bus();
        bus.subscribe(PaymentCaptured.class, ledger);
        bus.subscribe(PaymentCaptured.class, audit);                  // a handler of any event fits here
        Handler<? super PaymentCaptured> forCaptures = audit;         // the same subtyping, written out

        // Step 3: uncomment. A handler that only knows captures can't take every event.
        // Handler<? super PaymentEvent> tooWide = ledger;

        bus.publish(new PaymentCaptured("pay_7781", 1_999));
        bus.publish(new PaymentRefunded("pay_7781", 500));            // nobody subscribed to refunds
        forCaptures.handle(new PaymentCaptured("pay_7782", 250));

        System.out.println(Bus.class.getDeclaredMethod("subscribe", Class.class, Handler.class).toGenericString());
    }
}
