package workbench.reactive.l01;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Flow;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/** A fast oven and a slow packer, first with plain push, then with demand. */
public class DrowningDemo {
    static final int LOAVES = 100_000;

    public static void main(String[] args) throws Exception {
        pushWithoutDemand();
        pushWithDemand();
    }

    // Plain push: the oven hands every loaf to the packer's executor. Its queue has no limit.
    static void pushWithoutDemand() throws Exception {
        ExecutorService packer = Executors.newSingleThreadExecutor();
        AtomicLong boxed = new AtomicLong();
        long t0 = System.nanoTime();
        for (int i = 0; i < LOAVES; i++) {
            packer.execute(() -> { packLoaf(); boxed.incrementAndGet(); });
        }
        long ms = (System.nanoTime() - t0) / 1_000_000;
        long b = boxed.get();
        System.out.printf("plain push:  oven done in %,5d ms, packer boxed %,7d, %,6d loaves waiting in memory%n",
                ms, b, LOAVES - b);
        packer.shutdownNow();
    }

    // With demand: the packer asks for one loaf at a time. submit() blocks when the 256-slot buffer is full.
    static void pushWithDemand() throws Exception {
        AtomicLong boxed = new AtomicLong();
        long maxLag = 0;
        long t0 = System.nanoTime();
        try (SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>()) {
            publisher.subscribe(new Flow.Subscriber<Integer>() {
                Flow.Subscription s;
                public void onSubscribe(Flow.Subscription s) { this.s = s; s.request(1); }
                public void onNext(Integer loaf) { packLoaf(); boxed.incrementAndGet(); s.request(1); }
                public void onError(Throwable t) { t.printStackTrace(); }
                public void onComplete() { }
            });
            for (int i = 0; i < LOAVES; i++) {
                publisher.submit(i);                                   // waits while the buffer is full
                maxLag = Math.max(maxLag, publisher.estimateMaximumLag());
            }
            long ms = (System.nanoTime() - t0) / 1_000_000;
            long b = boxed.get();
            System.out.printf("with demand: oven done in %,5d ms, packer boxed %,7d, never more than %,d waiting%n",
                    ms, b, maxLag);
        }
        TimeUnit.MILLISECONDS.sleep(50);
    }

    // stands in for 10 microseconds of packing one loaf
    static void packLoaf() {
        long until = System.nanoTime() + 10_000;
        while (System.nanoTime() < until) Thread.onSpinWait();
    }
}
