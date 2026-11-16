// Java equivalent of CancelTable.kt: a loop is only as cancellable as its checks. Each worker
// interrupts its own thread at 3 (the closest thing to cancel()) and never blocks afterwards.
// The checked loop tests the interrupt flag before each item, the way ensureActive() tests the Job.
package workbench.flows.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.function.IntConsumer;

public class CancelTableJava {
    static List<Integer> run(boolean checked) throws InterruptedException {
        List<Integer> seen = new ArrayList<>();
        IntConsumer collector = v -> {
            seen.add(v);
            if (v == 3) Thread.currentThread().interrupt();       // "cancel" myself
        };
        Thread t = Thread.ofPlatform().start(() -> {
            for (int i = 1; i <= 5; i++) {
                if (checked && Thread.currentThread().isInterrupted()) return;   // like ensureActive()
                collector.accept(i);
            }
        });
        t.join();
        return seen;
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("loop that checks the interrupt flag " + run(true));
        System.out.println("loop with no check                  " + run(false));
    }
}
