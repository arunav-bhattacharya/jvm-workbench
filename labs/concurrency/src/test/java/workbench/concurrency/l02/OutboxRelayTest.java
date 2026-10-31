package workbench.concurrency.l02;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;

class OutboxRelayTest {
    // set when a test ends, so a relay that never stops is shut down by its own outbox
    private final AtomicBoolean closed = new AtomicBoolean();
    private final List<Thread> started = new ArrayList<>();

    private static final class TestOver extends RuntimeException {}

    private Thread startDaemon(Runnable r) {
        Thread t = new Thread(r, "relay-under-test");
        t.setDaemon(true);
        t.setUncaughtExceptionHandler((th, e) -> { });   // TestOver is how a stuck relay dies quietly
        t.start();
        started.add(t);
        return t;
    }

    @AfterEach
    void shutDownStragglers() {
        closed.set(true);
        started.forEach(Thread::interrupt);
    }

    /** An outbox that always has a full batch: the relay never sleeps. */
    private Supplier<List<String>> busyOutbox(int batchSize, CountDownLatch firstFetch) {
        List<String> batch = Collections.nCopies(batchSize, "payment-captured");
        return () -> {
            if (closed.get()) throw new TestOver();
            firstFetch.countDown();
            return batch;
        };
    }

    /** An outbox that is always empty: the relay spends its life sleeping. */
    private Supplier<List<String>> emptyOutbox(CountDownLatch firstFetch) {
        return () -> {
            if (closed.get()) throw new TestOver();
            firstFetch.countDown();
            return List.of();
        };
    }

    @Test
    @DisplayName("publishes every message in order, then stops when interrupted")
    void publishesThenStops() throws Exception {
        List<List<String>> batches = new ArrayList<>(List.of(List.of("m1", "m2", "m3"), List.of("m4"), List.of("m5", "m6", "m7")));
        List<String> published = new CopyOnWriteArrayList<>();
        CountDownLatch allSeven = new CountDownLatch(7);
        Supplier<List<String>> outbox = () -> {
            if (closed.get()) throw new TestOver();
            synchronized (batches) { return batches.isEmpty() ? List.of() : batches.remove(0); }
        };
        Thread t = startDaemon(new OutboxRelay(outbox, m -> { published.add(m); allSeven.countDown(); }, 20));

        assertThat(allSeven.await(5, TimeUnit.SECONDS)).as("all seven messages published").isTrue();
        t.interrupt();
        t.join(5_000);
        assertThat(published).containsExactly("m1", "m2", "m3", "m4", "m5", "m6", "m7");
        assertThat(t.isAlive()).as("relay still running 5 s after interrupt").isFalse();
    }

    @Test
    @DisplayName("stops when interrupted while sleeping, even with a 10 s idle pause")
    void stopsWhileIdle() throws Exception {
        CountDownLatch polled = new CountDownLatch(1);
        Thread t = startDaemon(new OutboxRelay(emptyOutbox(polled), m -> { }, 10_000));
        assertThat(polled.await(5, TimeUnit.SECONDS)).isTrue();

        t.interrupt();
        t.join(5_000);
        assertThat(t.isAlive()).as("relay still running 5 s after interrupt").isFalse();
    }

    @Test
    @DisplayName("stops when interrupted while busy, when it never reaches sleep()")
    void stopsWhileBusy() throws Exception {
        CountDownLatch polled = new CountDownLatch(1);
        AtomicInteger published = new AtomicInteger();
        Thread t = startDaemon(new OutboxRelay(busyOutbox(50, polled), m -> published.incrementAndGet(), 20));
        assertThat(polled.await(5, TimeUnit.SECONDS)).isTrue();

        t.interrupt();
        t.join(5_000);
        assertThat(t.isAlive()).as("relay still running 5 s after interrupt").isFalse();
    }

    @Test
    @DisplayName("finishes the batch in hand: never stops halfway through a batch")
    void finishesTheBatch() throws Exception {
        CountDownLatch polled = new CountDownLatch(1);
        AtomicInteger published = new AtomicInteger();
        Thread t = startDaemon(new OutboxRelay(busyOutbox(50, polled), m -> published.incrementAndGet(), 20));
        assertThat(polled.await(5, TimeUnit.SECONDS)).isTrue();

        t.interrupt();
        t.join(5_000);
        assertThat(t.isAlive()).as("relay still running 5 s after interrupt").isFalse();
        assertThat(published.get() % 50).as("messages published from a half-finished batch").isZero();
    }

    @Test
    @DisplayName("returns with the thread's interrupt flag still set")
    void restoresTheFlag() throws Exception {
        CountDownLatch polled = new CountDownLatch(1);
        AtomicReference<Boolean> flagAfterRun = new AtomicReference<>();
        OutboxRelay relay = new OutboxRelay(emptyOutbox(polled), m -> { }, 10_000);
        Thread t = startDaemon(() -> {
            relay.run();
            flagAfterRun.set(Thread.currentThread().isInterrupted());
        });
        assertThat(polled.await(5, TimeUnit.SECONDS)).isTrue();

        t.interrupt();
        t.join(5_000);
        assertThat(flagAfterRun.get()).as("interrupt flag when run() returned (null = never returned)").isTrue();
    }
}
