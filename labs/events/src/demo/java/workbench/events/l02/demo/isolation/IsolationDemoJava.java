package workbench.events.l02.demo.isolation;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

public class IsolationDemoJava {
    sealed interface ParcelEvent permits ParcelCollected { String parcelId(); }
    record ParcelCollected(String parcelId, long grams) implements ParcelEvent {}

    /** A list of handlers, stored in the list you pass; publish can isolate failures or not. */
    static final class Bus {
        private final List<Consumer<ParcelEvent>> handlers;
        private final boolean isolate;

        Bus(List<Consumer<ParcelEvent>> handlers, boolean isolate) { this.handlers = handlers; this.isolate = isolate; }

        AutoCloseable subscribe(Consumer<ParcelEvent> handler) {
            handlers.add(handler);
            return () -> handlers.remove(handler);
        }

        void publish(ParcelEvent event) {
            for (Consumer<ParcelEvent> h : handlers) {
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
            System.out.println("  welcome text, once");
            try { once.get().close(); } catch (Exception x) { throw new IllegalStateException(x); }
        }));
        bus.subscribe(e -> { throw new IllegalStateException("load board is down"); });
        bus.subscribe(e -> System.out.println("  text to sender: " + e.parcelId() + " is on its way"));
        try {
            bus.publish(new ParcelCollected("PP-7781", 2_500));
            bus.publish(new ParcelCollected("PP-7782", 1_200));
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
