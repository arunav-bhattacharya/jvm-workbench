package workbench.reactive.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Flow;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.TimeUnit;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BatchingSubscriberTest {

    /** Wraps a publisher so the test can see every request(n) the subscriber makes. */
    private static <T> Flow.Publisher<T> recordingRequests(Flow.Publisher<T> source, List<Long> requests) {
        return subscriber -> source.subscribe(new Flow.Subscriber<T>() {
            @Override public void onSubscribe(Flow.Subscription s) {
                subscriber.onSubscribe(new Flow.Subscription() {
                    @Override public void request(long n) { requests.add(n); s.request(n); }
                    @Override public void cancel() { s.cancel(); }
                });
            }
            @Override public void onNext(T item) { subscriber.onNext(item); }
            @Override public void onError(Throwable t) { subscriber.onError(t); }
            @Override public void onComplete() { subscriber.onComplete(); }
        });
    }

    /** A hand-held subscription for driving the subscriber directly. */
    private static final class FakeSubscription implements Flow.Subscription {
        final List<Long> requests = new ArrayList<>();
        boolean cancelled;
        @Override public void request(long n) { requests.add(n); }
        @Override public void cancel() { cancelled = true; }
    }

    @Test
    @DisplayName("Against a SubmissionPublisher: requests one batch up front, then one more after each full batch")
    void requestsInBatches() throws Exception {
        List<Long> requests = new CopyOnWriteArrayList<>();
        List<Integer> seen = new CopyOnWriteArrayList<>();
        BatchingSubscriber<Integer> subscriber = new BatchingSubscriber<>(4, seen::add);
        try (SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>()) {
            recordingRequests(publisher, requests).subscribe(subscriber);
            for (int i = 1; i <= 10; i++) publisher.submit(i);
        } // close() sends onComplete after the buffered items

        assertThat(subscriber.await(3, TimeUnit.SECONDS)).as("stream finished").isTrue();
        assertThat(seen).containsExactly(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
        // 4 up front, 4 after item 4, 4 after item 8. Never Long.MAX_VALUE, never one per item.
        assertThat(requests).containsExactly(4L, 4L, 4L);
        assertThat(subscriber.error()).isNull();
    }

    @Test
    @DisplayName("Against a SubmissionPublisher: 1,000 items arrive in order with 32 requests of 32")
    void thousandItems() throws Exception {
        List<Long> requests = new CopyOnWriteArrayList<>();
        List<Integer> seen = new CopyOnWriteArrayList<>();
        BatchingSubscriber<Integer> subscriber = new BatchingSubscriber<>(32, seen::add);
        try (SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>()) {
            recordingRequests(publisher, requests).subscribe(subscriber);
            for (int i = 0; i < 1_000; i++) publisher.submit(i);
        }

        assertThat(subscriber.await(3, TimeUnit.SECONDS)).as("stream finished").isTrue();
        assertThat(seen).containsExactlyElementsOf(IntStream.range(0, 1_000).boxed().toList());
        assertThat(requests).hasSize(32).containsOnly(32L);
    }

    @Test
    @DisplayName("A publisher error ends the stream and is reported by error()")
    void publisherError() throws Exception {
        BatchingSubscriber<String> subscriber = new BatchingSubscriber<>(8, s -> { });
        SubmissionPublisher<String> publisher = new SubmissionPublisher<>();
        publisher.subscribe(subscriber);
        publisher.submit("auth-1");
        publisher.closeExceptionally(new IllegalStateException("issuer feed down"));

        assertThat(subscriber.await(3, TimeUnit.SECONDS)).as("stream finished").isTrue();
        assertThat(subscriber.error()).hasMessage("issuer feed down");
    }

    @Test
    @DisplayName("A failing handler cancels the subscription, returns normally, and later items are ignored")
    void handlerFailureCancels() throws Exception {
        List<String> handled = new ArrayList<>();
        BatchingSubscriber<String> subscriber = new BatchingSubscriber<>(4, row -> {
            handled.add(row);
            if (row.equals("bad-row")) throw new IllegalArgumentException("cannot parse " + row);
        });
        FakeSubscription subscription = new FakeSubscription();
        subscriber.onSubscribe(subscription);

        subscriber.onNext("row-1");
        subscriber.onNext("bad-row");      // must not throw back into the publisher (rule 2.13)
        subscriber.onNext("row-3");        // already requested, so it may still arrive (rule 2.8)

        assertThat(subscription.cancelled).as("cancelled").isTrue();
        assertThat(handled).containsExactly("row-1", "bad-row");
        assertThat(subscriber.error()).isInstanceOf(IllegalArgumentException.class);
        assertThat(subscriber.await(0, TimeUnit.SECONDS)).as("finished").isTrue();
    }

    @Test
    @DisplayName("Rejects null items and cancels a second subscription (rules 2.13 and 2.5)")
    void nullsAndSecondSubscription() {
        BatchingSubscriber<String> subscriber = new BatchingSubscriber<>(2, s -> { });
        FakeSubscription first = new FakeSubscription();
        FakeSubscription second = new FakeSubscription();
        subscriber.onSubscribe(first);
        subscriber.onSubscribe(second);

        assertThat(first.requests).containsExactly(2L);
        assertThat(first.cancelled).isFalse();
        assertThat(second.cancelled).as("second subscription cancelled").isTrue();
        assertThat(second.requests).isEmpty();
        assertThatThrownBy(() -> subscriber.onNext(null)).isInstanceOf(NullPointerException.class);
    }
}
