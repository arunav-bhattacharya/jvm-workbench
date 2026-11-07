package workbench.generics.l11.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** Java twin of EventBusDemo.kt. The handler parameter says ? super E: Consumer Super. */
public class EventBusDemoJava {

    static final class Router {
        private final List<Consumer<PaymentEvent>> adapters = new ArrayList<>();

        <E extends PaymentEvent> void on(Class<E> type, Consumer<? super E> handler) {
            adapters.add(event -> {                               // takes any event...
                if (type.isInstance(event)) handler.accept(type.cast(event));   // ...passes on only an E
            });
        }

        void publish(PaymentEvent event) { adapters.forEach(a -> a.accept(event)); }
    }

    public static void main(String[] args) {
        Router router = new Router();
        Consumer<PaymentEvent> auditAll = e -> System.out.println("audit " + e.getPaymentId());
        router.on(CardAuthorized.class, e -> System.out.println("fraud check " + e.getCents()));
        router.on(CardAuthorized.class, auditAll);
        router.on(RefundIssued.class, e -> System.out.println("refund " + e.getCents()));

        router.publish(new CardAuthorized("pay_1", 1_200));
        router.publish(new RefundIssued("pay_2", 500));
    }
}
