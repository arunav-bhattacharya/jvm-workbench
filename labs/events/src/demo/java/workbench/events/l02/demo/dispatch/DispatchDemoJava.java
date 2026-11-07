package workbench.events.l02.demo.dispatch;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

public class DispatchDemoJava {
    sealed interface PaymentEvent permits PaymentAuthorized, PaymentDeclined, MoneyMovement { String paymentId(); }
    record PaymentAuthorized(String paymentId, long cents) implements PaymentEvent {}
    record PaymentDeclined(String paymentId, String reason) implements PaymentEvent {}
    sealed interface MoneyMovement extends PaymentEvent permits PaymentCaptured, PaymentRefunded { long cents(); }
    record PaymentCaptured(String paymentId, long cents) implements MoneyMovement {}
    record PaymentRefunded(String paymentId, long cents) implements MoneyMovement {}

    /** Keys every handler by the class it was subscribed under; delivery can look up keys two ways. */
    static final class Bus {
        private final Map<Class<?>, List<Consumer<PaymentEvent>>> handlers = new HashMap<>();
        private final boolean walkSupertypes;

        Bus(boolean walkSupertypes) { this.walkSupertypes = walkSupertypes; }

        <E extends PaymentEvent> void subscribe(Class<E> type, Consumer<? super E> handler) {
            handlers.computeIfAbsent(type, t -> new ArrayList<>()).add(event -> handler.accept(type.cast(event)));
        }

        void publish(PaymentEvent event) {
            List<Class<?>> keys = walkSupertypes ? dispatchKeys(event.getClass()) : List.of(event.getClass());
            for (Class<?> key : keys) handlers.getOrDefault(key, List.of()).forEach(h -> h.accept(event));
        }
    }

    /** The event's class, then its supertypes that are events, nearest first. */
    static List<Class<?>> dispatchKeys(Class<?> type) {
        LinkedHashSet<Class<?>> found = new LinkedHashSet<>();
        ArrayDeque<Class<?>> queue = new ArrayDeque<>(List.of(type));
        while (!queue.isEmpty()) {
            Class<?> c = queue.removeFirst();
            if (!PaymentEvent.class.isAssignableFrom(c) || !found.add(c)) continue;
            queue.addAll(List.of(c.getInterfaces()));
            if (c.getSuperclass() != null) queue.add(c.getSuperclass());
        }
        return List.copyOf(found);
    }

    public static void main(String[] args) {
        for (boolean walk : new boolean[] {false, true}) {
            List<String> ran = new ArrayList<>();
            Bus bus = new Bus(walk);
            bus.subscribe(PaymentEvent.class, e -> ran.add("audit"));
            bus.subscribe(MoneyMovement.class, e -> ran.add("movements"));
            bus.subscribe(PaymentCaptured.class, e -> ran.add("ledger"));
            bus.publish(new PaymentCaptured("pay_7781", 1_999));
            System.out.printf("%-22s %s%n", walk ? "walking supertypes:" : "exact class only:", ran);
        }
        System.out.println("keys for PaymentCaptured: " + dispatchKeys(PaymentCaptured.class).stream().map(Class::getSimpleName).toList());
        System.out.println("keys for PaymentDeclined: " + dispatchKeys(PaymentDeclined.class).stream().map(Class::getSimpleName).toList());
    }
}
