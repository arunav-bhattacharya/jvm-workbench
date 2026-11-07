package workbench.reactive.l08;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.Disposable;
import reactor.core.publisher.Mono;
import reactor.test.publisher.TestPublisher;
import reactor.test.scheduler.VirtualTimeScheduler;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class HotPublishersTest {

    @AfterEach
    void resetClock() {
        VirtualTimeScheduler.reset();
    }

    static PaymentEvent event(int n) {
        return new PaymentEvent("pay-" + n, "authorized");
    }

    @Test
    @DisplayName("live() is hot: each subscriber sees only the events published after it subscribed")
    void lateSubscriberSeesOnlyNewEvents() {
        PaymentEventHub hub = new PaymentEventHub();
        List<PaymentEvent> early = new CopyOnWriteArrayList<>();
        List<PaymentEvent> late = new CopyOnWriteArrayList<>();

        hub.publish(event(0));                                         // nobody is listening yet
        hub.live().subscribe(early::add);
        hub.publish(event(1));
        hub.live().subscribe(late::add);
        hub.publish(event(2));

        assertThat(early).containsExactly(event(1), event(2));
        assertThat(late).containsExactly(event(2));
    }

    @Test
    @DisplayName("live() keeps working after every subscriber has left")
    void hubSurvivesAnEmptyRoom() {
        PaymentEventHub hub = new PaymentEventHub();
        hub.live().subscribe().dispose();                              // the only dashboard disconnects
        List<PaymentEvent> next = new CopyOnWriteArrayList<>();
        AtomicInteger completions = new AtomicInteger();

        hub.live().subscribe(next::add, e -> { }, completions::incrementAndGet);
        hub.publish(event(7));

        assertThat(completions).as("completions seen by the new dashboard").hasValue(0);
        assertThat(next).containsExactly(event(7));
    }

    @Test
    @DisplayName("publish() from 8 threads at once loses no event (8 x 2,000)")
    void concurrentPublishersLoseNothing() throws InterruptedException {
        PaymentEventHub hub = new PaymentEventHub();
        AtomicInteger received = new AtomicInteger();
        hub.live().subscribe(e -> received.incrementAndGet());

        CountDownLatch go = new CountDownLatch(1);
        List<Thread> threads = new CopyOnWriteArrayList<>();
        AtomicInteger crashed = new AtomicInteger();
        for (int t = 0; t < 8; t++) {
            Thread thread = new Thread(() -> {
                try {
                    go.await();
                    for (int i = 0; i < 2_000; i++) hub.publish(event(i));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } catch (RuntimeException e) {
                    crashed.incrementAndGet();                         // e.g. an EmissionException from FAIL_FAST
                }
            });
            thread.start();
            threads.add(thread);
        }
        go.countDown();
        for (Thread t : threads) t.join();

        assertThat(crashed).as("publisher threads that died with an exception").hasValue(0);
        assertThat(received).as("events received").hasValue(16_000);
    }

    @Test
    @DisplayName("shareWithLatest opens one connection, and a late subscriber gets the latest rate at once")
    void oneConnectionAndLatestForLateSubscribers() {
        TestPublisher<String> provider = TestPublisher.create();
        AtomicInteger connections = new AtomicInteger();
        var shared = RateFeeds.shareWithLatest(provider.flux().doOnSubscribe(s -> connections.incrementAndGet()));
        List<String> a = new CopyOnWriteArrayList<>();
        List<String> b = new CopyOnWriteArrayList<>();

        Disposable first = shared.subscribe(a::add);
        provider.next("1.0811", "1.0812");
        Disposable second = shared.subscribe(b::add);
        assertThat(b).as("late subscriber, right after subscribing").containsExactly("1.0812");
        provider.next("1.0813");

        assertThat(a).containsExactly("1.0811", "1.0812", "1.0813");
        assertThat(b).containsExactly("1.0812", "1.0813");
        assertThat(connections).as("connections to the provider").hasValue(1);
        first.dispose();
        second.dispose();
    }

    @Test
    @DisplayName("shareWithLatest closes the connection when the last subscriber leaves")
    void lastSubscriberLeavingCancelsUpstream() {
        TestPublisher<String> provider = TestPublisher.create();
        var shared = RateFeeds.shareWithLatest(provider.flux());

        Disposable first = shared.subscribe();
        Disposable second = shared.subscribe();
        provider.next("1.0811");
        first.dispose();
        assertThat(provider.wasCancelled()).as("cancelled while one subscriber remains").isFalse();
        second.dispose();
        assertThat(provider.wasCancelled()).as("cancelled after the last subscriber left").isTrue();
    }

    @Test
    @DisplayName("cacheFor loads once per ttl: cached at 4 minutes, reloaded after 5")
    void cacheExpires() {
        VirtualTimeScheduler clock = VirtualTimeScheduler.getOrSet();     // Reactor's timers now use this clock
        AtomicInteger loads = new AtomicInteger();
        Mono<Integer> fees = RateFeeds.cacheFor(Mono.fromCallable(loads::incrementAndGet), Duration.ofMinutes(5));
        assertThat(loads).as("loads before anyone subscribes").hasValue(0);

        assertThat(fees.block(Duration.ofSeconds(1))).isEqualTo(1);
        assertThat(fees.block(Duration.ofSeconds(1))).as("second read, same minute").isEqualTo(1);
        clock.advanceTimeBy(Duration.ofMinutes(4));
        assertThat(fees.block(Duration.ofSeconds(1))).as("after 4 minutes").isEqualTo(1);
        clock.advanceTimeBy(Duration.ofMinutes(2));
        assertThat(fees.block(Duration.ofSeconds(1))).as("after 6 minutes").isEqualTo(2);
        assertThat(loads).hasValue(2);
    }
}
