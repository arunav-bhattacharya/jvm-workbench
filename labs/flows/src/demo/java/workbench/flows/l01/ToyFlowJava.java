// Java equivalent of ToyFlow.kt: the same two interfaces, pushing values with a plain method call.
// One difference: this emit blocks the thread while the collector works. In Kotlin emit is a
// suspend call, so a collector that waits (delay, I/O) gives the thread back meanwhile.
package workbench.flows.l01;

import java.util.function.Function;

public class ToyFlowJava {
    interface ToyCollector<T> {
        void emit(T value);
    }

    // one abstract method, so Java takes a lambda for it
    interface ToyFlow<T> {
        void collect(ToyCollector<T> collector);

        // map is a collector wrapped in a collector
        default <R> ToyFlow<R> map(Function<T, R> transform) {
            return downstream -> this.collect(value -> downstream.emit(transform.apply(value)));
        }
    }

    public static void main(String[] args) {
        ToyFlow<Integer> dishes = collector -> {
            System.out.println("  [producer] start");
            for (int id = 1; id <= 3; id++) {
                System.out.println("  [producer] before emit(" + id + ")");
                collector.emit(id);
                System.out.println("  [producer] after emit(" + id + ")");
            }
            System.out.println("  [producer] done");
        };
        System.out.println("built the flow, nothing ran yet");

        System.out.println("--- first collect, through map");
        dishes.map(id -> id * 100).collect(v -> System.out.println("  [collector] got " + v));

        System.out.println("--- second collect: the body runs again");
        dishes.collect(v -> System.out.println("  [collector] got " + v));
    }
}
