package workbench.reactive.l01;

import java.util.concurrent.Flow;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.atomic.AtomicInteger;

/** A SubmissionPublisher with a 2-slot buffer and a subscriber that never asks for anything. */
public class SaturationDemo {
    public static void main(String[] args) {
        System.out.println("default buffer: " + Flow.defaultBufferSize());
        AtomicInteger dropped = new AtomicInteger();
        try (SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>(ForkJoinPool.commonPool(), 2)) {
            publisher.subscribe(new Flow.Subscriber<Integer>() {
                public void onSubscribe(Flow.Subscription s) { }              // never calls request(n)
                public void onNext(Integer item) { System.out.println("got " + item); }
                public void onError(Throwable t) { }
                public void onComplete() { }
            });
            for (int i = 1; i <= 10; i++) {
                // offer() does not block. When the buffer is full it calls the drop handler instead.
                int lag = publisher.offer(i, (subscriber, item) -> {
                    dropped.incrementAndGet();
                    return false;                                             // false: don't retry, drop it
                });
                System.out.printf("offer(%d) -> %d%n", i, lag);
            }
            System.out.println("dropped " + dropped.get() + " of 10, lag " + publisher.estimateMaximumLag());
        }
    }
}
