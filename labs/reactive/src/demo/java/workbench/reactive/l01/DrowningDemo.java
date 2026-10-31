package workbench.reactive.l01;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Flow;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/** A fast producer and a slow ledger writer, first with plain push, then with demand. */
public class DrowningDemo {
    static final int EVENTS = 100_000;

    public static void main(String[] args) throws Exception {
        pushWithoutDemand();
        pushWithDemand();
    }

    // Plain push: the producer hands every event to the writer's executor. Its queue has no limit.
    static void pushWithoutDemand() throws Exception {
        ExecutorService writer = Executors.newSingleThreadExecutor();
        AtomicLong written = new AtomicLong();
        long t0 = System.nanoTime();
        for (int i = 0; i < EVENTS; i++) {
            writer.execute(() -> { writeToLedger(); written.incrementAndGet(); });
        }
        long ms = (System.nanoTime() - t0) / 1_000_000;
        long w = written.get();
        System.out.printf("plain push:  producer done in %,5d ms, ledger wrote %,6d, %,6d events waiting in memory%n",
                ms, w, EVENTS - w);
        writer.shutdownNow();
    }

    // With demand: the writer asks for one event at a time. submit() blocks when the 256-slot buffer is full.
    static void pushWithDemand() throws Exception {
        AtomicLong written = new AtomicLong();
        long maxLag = 0;
        long t0 = System.nanoTime();
        try (SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>()) {
            publisher.subscribe(new Flow.Subscriber<Integer>() {
                Flow.Subscription s;
                public void onSubscribe(Flow.Subscription s) { this.s = s; s.request(1); }
                public void onNext(Integer event) { writeToLedger(); written.incrementAndGet(); s.request(1); }
                public void onError(Throwable t) { t.printStackTrace(); }
                public void onComplete() { }
            });
            for (int i = 0; i < EVENTS; i++) {
                publisher.submit(i);                                   // waits while the buffer is full
                maxLag = Math.max(maxLag, publisher.estimateMaximumLag());
            }
            long ms = (System.nanoTime() - t0) / 1_000_000;
            long w = written.get();
            System.out.printf("with demand: producer done in %,5d ms, ledger wrote %,6d, never more than %,d waiting%n",
                    ms, w, maxLag);
        }
        TimeUnit.MILLISECONDS.sleep(50);
    }

    // stands in for a 10-microsecond ledger write
    static void writeToLedger() {
        long until = System.nanoTime() + 10_000;
        while (System.nanoTime() < until) Thread.onSpinWait();
    }
}
