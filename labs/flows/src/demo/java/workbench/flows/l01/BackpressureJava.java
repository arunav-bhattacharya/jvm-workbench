// Java equivalent of Backpressure.kt: the hand-written push flow with Thread.sleep in real time.
// The cook needs 100 ms per dish, the diner 300 ms to eat it. Here the thread is
// blocked during both sleeps; in Kotlin's delay it would be free for other coroutines.
package workbench.flows.l01;

public class BackpressureJava {
    interface ToyCollector<T> {
        void emit(T value);
    }

    interface ToyFlow<T> {
        void collect(ToyCollector<T> collector);
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    public static void main(String[] args) {
        long t0 = System.currentTimeMillis();
        ToyFlow<Integer> dishes = collector -> {
            for (int id = 1; id <= 3; id++) {
                sleep(100);
                System.out.printf("  t=%4d emit %d%n", System.currentTimeMillis() - t0, id);
                collector.emit(id);
            }
        };
        dishes.collect(id -> {
            sleep(300);
            System.out.printf("  t=%4d eaten  %d%n", System.currentTimeMillis() - t0, id);
        });
        System.out.printf("  total %d ms (real time, so a little more than 1200)%n", System.currentTimeMillis() - t0);
    }
}
