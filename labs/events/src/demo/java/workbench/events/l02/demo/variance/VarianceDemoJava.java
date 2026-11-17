package workbench.events.l02.demo.variance;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class VarianceDemoJava {
    sealed interface ParcelEvent permits ParcelCollected, ParcelDelivered { String parcelId(); }
    record ParcelCollected(String parcelId, long grams) implements ParcelEvent {}
    record ParcelDelivered(String parcelId, long grams) implements ParcelEvent {}

    /** Java interfaces have no declaration-site variance: every use site says ? super. */
    @FunctionalInterface
    interface Handler<E extends ParcelEvent> {
        void handle(E event);
    }

    static final class Bus {
        private final List<Map.Entry<Class<?>, Handler<ParcelEvent>>> handlers = new ArrayList<>();

        // Step 2: change Handler<? super E> to Handler<E> and run again.
        <E extends ParcelEvent> void subscribe(Class<E> type, Handler<? super E> handler) {
            handlers.add(Map.entry(type, event -> handler.handle(type.cast(event))));
        }

        void publish(ParcelEvent event) {
            for (var entry : handlers) if (entry.getKey().isInstance(event)) entry.getValue().handle(event);
        }
    }

    public static void main(String[] args) throws Exception {
        Handler<ParcelEvent> tracking = e -> System.out.println("tracking " + e.parcelId() + " (" + e.getClass().getSimpleName() + ")");
        Handler<ParcelCollected> load = e -> System.out.println("load     +" + e.grams() + " g");

        Bus bus = new Bus();
        bus.subscribe(ParcelCollected.class, load);
        bus.subscribe(ParcelCollected.class, tracking);                 // a handler of any event fits here
        Handler<? super ParcelCollected> forCollections = tracking;     // the same subtyping, written out

        // Step 3: uncomment. A handler that only knows collections can't take every event.
        // Handler<? super ParcelEvent> tooWide = load;

        bus.publish(new ParcelCollected("PP-7781", 2_500));
        bus.publish(new ParcelDelivered("PP-7781", 2_500));             // nobody subscribed to deliveries
        forCollections.handle(new ParcelCollected("PP-7782", 1_200));

        System.out.println(Bus.class.getDeclaredMethod("subscribe", Class.class, Handler.class).toGenericString());
    }
}
