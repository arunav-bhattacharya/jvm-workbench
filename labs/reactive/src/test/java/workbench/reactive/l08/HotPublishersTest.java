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

    static OrderEvent event(int n) {
        return new OrderEvent("order-" + n, "placed");
    }

    @Test
    @DisplayName("live() is hot: each listener hears only the events rung after it subscribed")
    void lateSubscriberSeesOnlyNewEvents() {
        OrderBell bell = new OrderBell();
        List<OrderEvent> early = new CopyOnWriteArrayList<>();
        List<OrderEvent> late = new CopyOnWriteArrayList<>();

        bell.ring(event(0));                                           // nobody is listening yet
        bell.live().subscribe(early::add);
        bell.ring(event(1));
        bell.live().subscribe(late::add);
        bell.ring(event(2));

        assertThat(early).containsExactly(event(1), event(2));
        assertThat(late).containsExactly(event(2));
    }

    @Test
    @DisplayName("live() keeps working after every listener has left")
    void bellSurvivesAnEmptyRoom() {
        OrderBell bell = new OrderBell();
        bell.live().subscribe().dispose();                             // the only screen switches off
        List<OrderEvent> next = new CopyOnWriteArrayList<>();
        AtomicInteger completions = new AtomicInteger();

        bell.live().subscribe(next::add, e -> { }, completions::incrementAndGet);
        bell.ring(event(7));

        assertThat(completions).as("completions seen by the new screen").hasValue(0);
        assertThat(next).containsExactly(event(7));
    }

    @Test
    @DisplayName("ring() from 8 threads at once loses no event (8 x 2,000)")
    void concurrentRingersLoseNothing() throws InterruptedException {
        OrderBell bell = new OrderBell();
        AtomicInteger received = new AtomicInteger();
        bell.live().subscribe(e -> received.incrementAndGet());

        CountDownLatch go = new CountDownLatch(1);
        List<Thread> threads = new CopyOnWriteArrayList<>();
        AtomicInteger crashed = new AtomicInteger();
        for (int t = 0; t < 8; t++) {
            Thread thread = new Thread(() -> {
                try {
                    go.await();
                    for (int i = 0; i < 2_000; i++) bell.ring(event(i));
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

        assertThat(crashed).as("till threads that died with an exception").hasValue(0);
        assertThat(received).as("events received").hasValue(16_000);
    }

    @Test
    @DisplayName("shareWithLatest opens one connection, and a late subscriber gets the latest reading at once")
    void oneConnectionAndLatestForLateSubscribers() {
        TestPublisher<String> thermometer = TestPublisher.create();
        AtomicInteger connections = new AtomicInteger();
        var shared = SharedFeeds.shareWithLatest(thermometer.flux().doOnSubscribe(s -> connections.incrementAndGet()));
        List<String> a = new CopyOnWriteArrayList<>();
        List<String> b = new CopyOnWriteArrayList<>();

        Disposable first = shared.subscribe(a::add);
        thermometer.next("201", "202");
        Disposable second = shared.subscribe(b::add);
        assertThat(b).as("late subscriber, right after subscribing").containsExactly("202");
        thermometer.next("203");

        assertThat(a).containsExactly("201", "202", "203");
        assertThat(b).containsExactly("202", "203");
        assertThat(connections).as("connections to the thermometer").hasValue(1);
        first.dispose();
        second.dispose();
    }

    @Test
    @DisplayName("shareWithLatest closes the connection when the last subscriber leaves")
    void lastSubscriberLeavingCancelsUpstream() {
        TestPublisher<String> thermometer = TestPublisher.create();
        var shared = SharedFeeds.shareWithLatest(thermometer.flux());

        Disposable first = shared.subscribe();
        Disposable second = shared.subscribe();
        thermometer.next("201");
        first.dispose();
        assertThat(thermometer.wasCancelled()).as("cancelled while one subscriber remains").isFalse();
        second.dispose();
        assertThat(thermometer.wasCancelled()).as("cancelled after the last subscriber left").isTrue();
    }

    @Test
    @DisplayName("cacheFor loads once per ttl: cached at 4 minutes, reloaded after 5")
    void cacheExpires() {
        VirtualTimeScheduler clock = VirtualTimeScheduler.getOrSet();     // Reactor's timers now use this clock
        AtomicInteger loads = new AtomicInteger();
        Mono<Integer> prices = SharedFeeds.cacheFor(Mono.fromCallable(loads::incrementAndGet), Duration.ofMinutes(5));
        assertThat(loads).as("loads before anyone subscribes").hasValue(0);

        assertThat(prices.block(Duration.ofSeconds(1))).isEqualTo(1);
        assertThat(prices.block(Duration.ofSeconds(1))).as("second read, same minute").isEqualTo(1);
        clock.advanceTimeBy(Duration.ofMinutes(4));
        assertThat(prices.block(Duration.ofSeconds(1))).as("after 4 minutes").isEqualTo(1);
        clock.advanceTimeBy(Duration.ofMinutes(2));
        assertThat(prices.block(Duration.ofSeconds(1))).as("after 6 minutes").isEqualTo(2);
        assertThat(loads).hasValue(2);
    }
}
