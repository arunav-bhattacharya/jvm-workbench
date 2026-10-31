package workbench.reactive.l01;

import java.util.Objects;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Flow;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

public class BatchingSubscriber<T> implements Flow.Subscriber<T> {
    private final int batchSize;
    private final Consumer<? super T> handler;
    private final CountDownLatch done = new CountDownLatch(1);
    private Flow.Subscription subscription;
    private int handledInBatch;
    private boolean cancelled;
    private volatile Throwable error;

    public BatchingSubscriber(int batchSize, Consumer<? super T> handler) {
        if (batchSize <= 0) throw new IllegalArgumentException("batchSize must be positive: " + batchSize);
        this.batchSize = batchSize;
        this.handler = Objects.requireNonNull(handler);
    }

    @Override
    public void onSubscribe(Flow.Subscription subscription) {
        Objects.requireNonNull(subscription);
        if (this.subscription != null) {        // rule 2.5: we already have one, so refuse the second
            subscription.cancel();
            return;
        }
        this.subscription = subscription;
        subscription.request(batchSize);        // 1. ask for the first batch, never "everything"
    }

    @Override
    public void onNext(T item) {
        Objects.requireNonNull(item);           // rule 2.13: null items are a publisher bug
        if (cancelled) return;                  // rule 2.8: items may still arrive after cancel
        try {
            handler.accept(item);               // 2. do the work
        } catch (Throwable t) {
            cancelled = true;                   // 3. the only legal way to say "stop" is cancel()
            subscription.cancel();
            error = t;
            done.countDown();
            return;                             // rule 2.13: return normally, never throw back
        }
        if (++handledInBatch == batchSize) {    // 4. a whole batch is done: ask for the next one
            handledInBatch = 0;
            subscription.request(batchSize);
        }
    }

    @Override
    public void onError(Throwable throwable) {
        Objects.requireNonNull(throwable);
        if (error == null) error = throwable;   // keep the first failure, ours or the publisher's
        done.countDown();
    }

    @Override
    public void onComplete() {
        done.countDown();
    }

    public boolean await(long timeout, TimeUnit unit) throws InterruptedException {
        return done.await(timeout, unit);
    }

    public Throwable error() {
        return error;
    }
}
