package workbench.vthreads.l02;

import java.util.ArrayDeque;
import java.util.Comparator;
import java.util.PriorityQueue;

public final class ToyScheduler {
    // a parked fiber: when it wants to wake, and a sequence number so equal times keep sleep order
    private record Parked(long wakeAt, long seq, Fiber fiber) {}

    private final ArrayDeque<Fiber> ready = new ArrayDeque<>();
    private final PriorityQueue<Parked> sleeping = new PriorityQueue<>(
            Comparator.comparingLong(Parked::wakeAt).thenComparingLong(Parked::seq));
    private long now;
    private long seq;

    public void spawn(Fiber fiber) {
        ready.addLast(fiber);
    }

    public long now() {
        return now;
    }

    public int run() {
        int mounts = 0;
        while (!ready.isEmpty() || !sleeping.isEmpty()) {
            if (ready.isEmpty()) {
                // 1. nothing can run: jump the clock to the next wake-up and make everyone due ready
                now = sleeping.peek().wakeAt();
                while (!sleeping.isEmpty() && sleeping.peek().wakeAt() <= now) {
                    ready.addLast(sleeping.poll().fiber());
                }
            }
            // 2. mount: run the next fiber on this thread until its next blocking point
            Fiber fiber = ready.pollFirst();
            mounts++;
            Step step = fiber.resume();
            // 3. unmount: a sleeper goes to the timer queue, a finished fiber is dropped
            switch (step) {
                case Step.Sleep s -> sleeping.add(new Parked(now + s.millis(), seq++, fiber));
                case Step.Done d -> { }
            }
        }
        return mounts;
    }
}
