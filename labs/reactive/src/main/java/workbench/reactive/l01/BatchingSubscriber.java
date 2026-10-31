package workbench.reactive.l01;

import java.util.Objects;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Flow;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

/**
 * A {@link Flow.Subscriber} that asks for items in batches, so the publisher can never
 * get more than {@code batchSize} items ahead of the handler.
 *
 * <p>Write the four {@code Flow.Subscriber} methods so that:
 * <ul>
 *   <li>{@code onSubscribe} keeps the subscription and requests one batch. If a subscription is
 *       already active, it cancels the new one instead (rule 2.5).</li>
 *   <li>{@code onNext} passes the item to the handler, and requests the next batch only after
 *       a whole batch has been handled.</li>
 *   <li>If the handler throws, {@code onNext} must still return normally (rule 2.13). Cancel the
 *       subscription, record the error, finish, and ignore any item that still arrives (rule 2.8).</li>
 *   <li>A {@code null} item or error is a broken publisher: throw {@link NullPointerException} (rule 2.13).</li>
 *   <li>{@code onError} records the error and finishes. {@code onComplete} finishes.</li>
 * </ul>
 * "Finish" means count down {@code done}, so {@link #await} returns.
 */
public class BatchingSubscriber<T> implements Flow.Subscriber<T> {
    private final int batchSize;
    private final Consumer<? super T> handler;
    private final CountDownLatch done = new CountDownLatch(1);
    // Signals arrive serially (rule 1.3), so plain fields are enough for the subscriber's own state.
    private Flow.Subscription subscription;
    private volatile Throwable error;

    public BatchingSubscriber(int batchSize, Consumer<? super T> handler) {
        if (batchSize <= 0) throw new IllegalArgumentException("batchSize must be positive: " + batchSize);
        this.batchSize = batchSize;
        this.handler = Objects.requireNonNull(handler);
    }

    @Override
    public void onSubscribe(Flow.Subscription subscription) {
        throw new UnsupportedOperationException("TODO: keep the subscription and request one batch");
    }

    @Override
    public void onNext(T item) {
        throw new UnsupportedOperationException("TODO: handle the item; request the next batch after a full batch");
    }

    @Override
    public void onError(Throwable throwable) {
        throw new UnsupportedOperationException("TODO: record the error and finish");
    }

    @Override
    public void onComplete() {
        throw new UnsupportedOperationException("TODO: finish");
    }

    /** Waits until the stream has finished (completed, failed, or been cancelled by a handler failure). */
    public boolean await(long timeout, TimeUnit unit) throws InterruptedException {
        return done.await(timeout, unit);
    }

    /** The error that ended the stream, or null if it completed normally or is still running. */
    public Throwable error() {
        return error;
    }
}
