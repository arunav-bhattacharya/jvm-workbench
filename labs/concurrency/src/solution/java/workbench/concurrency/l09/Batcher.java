package workbench.concurrency.l09;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

public class Batcher<T> {
    private final BlockingQueue<T> queue;

    public Batcher(int capacity) {
        if (capacity < 1) throw new IllegalArgumentException("capacity must be at least 1, was " + capacity);
        this.queue = new ArrayBlockingQueue<>(capacity);    // bounded: a slow writer pushes back on producers
    }

    public boolean submit(T entry) {
        return queue.offer(entry);                          // full? false at once, never blocks
    }

    public List<T> nextBatch(int max, Duration maxWait) throws InterruptedException {
        List<T> batch = new ArrayList<>(max);
        T first = queue.poll(maxWait.toNanos(), TimeUnit.NANOSECONDS);   // 1. wait for the first entry
        if (first == null) return batch;                                  //    nothing came: empty batch
        batch.add(first);
        queue.drainTo(batch, max - 1);                                    // 2. take what is already there, no waiting
        return batch;
    }

    public int pending() {
        return queue.size();
    }
}
