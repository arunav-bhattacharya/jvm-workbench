package workbench.patterns.l08;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/** A hand-rolled Observer: subscribe returns a handle, and one bad listener can't starve the rest. */
public class EventBusDemo {

    static final class EventBus<E> {
        private final List<Consumer<? super E>> listeners = new CopyOnWriteArrayList<>();

        AutoCloseable subscribe(Consumer<? super E> listener) {
            listeners.add(listener);
            return () -> listeners.remove(listener);             // the handle that prevents leaks
        }

        void publish(E event) {
            for (Consumer<? super E> l : listeners) {
                try {
                    l.accept(event);
                } catch (RuntimeException e) {                    // isolate each listener
                    System.out.println("  (a listener failed: " + e.getMessage() + ")");
                }
            }
        }
    }

    record Posted(String account, long amountMinor) {}

    public static void main(String[] args) throws Exception {
        EventBus<Posted> bus = new EventBus<>();
        bus.subscribe(e -> System.out.println("ledger view got  " + e));
        bus.subscribe(e -> { throw new IllegalStateException("analytics dashboard is down"); });
        AutoCloseable email = bus.subscribe(e -> System.out.println("email sender got " + e));

        bus.publish(new Posted("acc-1", 450));
        email.close();                                            // unsubscribe
        bus.publish(new Posted("acc-1", 900));
    }
}
