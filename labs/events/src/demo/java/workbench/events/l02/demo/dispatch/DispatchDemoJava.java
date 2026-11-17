package workbench.events.l02.demo.dispatch;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

public class DispatchDemoJava {
    sealed interface ParcelEvent permits ParcelBooked, DeliveryFailed, Handover { String parcelId(); }
    record ParcelBooked(String parcelId, long grams) implements ParcelEvent {}
    record DeliveryFailed(String parcelId, String reason) implements ParcelEvent {}
    sealed interface Handover extends ParcelEvent permits ParcelCollected, ParcelDelivered { long grams(); }
    record ParcelCollected(String parcelId, long grams) implements Handover {}
    record ParcelDelivered(String parcelId, long grams) implements Handover {}

    /** Keys every handler by the class it was subscribed under; delivery can look up keys two ways. */
    static final class Bus {
        private final Map<Class<?>, List<Consumer<ParcelEvent>>> handlers = new HashMap<>();
        private final boolean walkSupertypes;

        Bus(boolean walkSupertypes) { this.walkSupertypes = walkSupertypes; }

        <E extends ParcelEvent> void subscribe(Class<E> type, Consumer<? super E> handler) {
            handlers.computeIfAbsent(type, t -> new ArrayList<>()).add(event -> handler.accept(type.cast(event)));
        }

        void publish(ParcelEvent event) {
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
            if (!ParcelEvent.class.isAssignableFrom(c) || !found.add(c)) continue;
            queue.addAll(List.of(c.getInterfaces()));
            if (c.getSuperclass() != null) queue.add(c.getSuperclass());
        }
        return List.copyOf(found);
    }

    public static void main(String[] args) {
        for (boolean walk : new boolean[] {false, true}) {
            List<String> ran = new ArrayList<>();
            Bus bus = new Bus(walk);
            bus.subscribe(ParcelEvent.class, e -> ran.add("tracking"));
            bus.subscribe(Handover.class, e -> ran.add("handovers"));
            bus.subscribe(ParcelCollected.class, e -> ran.add("load"));
            bus.publish(new ParcelCollected("PP-7781", 2_500));
            System.out.printf("%-22s %s%n", walk ? "walking supertypes:" : "exact class only:", ran);
        }
        System.out.println("keys for ParcelCollected: " + dispatchKeys(ParcelCollected.class).stream().map(Class::getSimpleName).toList());
        System.out.println("keys for DeliveryFailed: " + dispatchKeys(DeliveryFailed.class).stream().map(Class::getSimpleName).toList());
    }
}
