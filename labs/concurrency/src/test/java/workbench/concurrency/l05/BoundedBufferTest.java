package workbench.concurrency.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicIntegerArray;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class BoundedBufferTest {

    private static Thread daemon(Runnable r) {
        Thread t = new Thread(r);
        t.setDaemon(true);
        t.start();
        return t;
    }

    /** Polls until the thread parks in wait(). Generous: a loaded machine can be slow to get there. */
    private static boolean reachesWaiting(Thread t) throws InterruptedException {
        for (int i = 0; i < 500; i++) {
            if (t.getState() == Thread.State.WAITING) return true;
            Thread.sleep(10);
        }
        return false;
    }

    @Test
    @DisplayName("hands items out in the order they were put in")
    void fifo() throws Exception {
        BoundedBuffer<String> buffer = new BoundedBuffer<>(3);
        buffer.put("auth-1");
        buffer.put("auth-2");
        buffer.put("auth-3");
        assertThat(buffer.size()).isEqualTo(3);
        assertThat(List.of(buffer.take(), buffer.take(), buffer.take())).containsExactly("auth-1", "auth-2", "auth-3");
        assertThat(buffer.size()).isZero();
    }

    @Test
    @DisplayName("take() waits (in WAITING, not spinning) while empty, and returns when an item arrives")
    void takeWaitsWhileEmpty() throws Exception {
        BoundedBuffer<String> buffer = new BoundedBuffer<>(2);
        AtomicReference<String> got = new AtomicReference<>();
        Thread consumer = daemon(() -> {
            try { got.set(buffer.take()); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        assertThat(reachesWaiting(consumer)).as("consumer parked in wait()").isTrue();
        buffer.put("auth-9");
        consumer.join(5_000);
        assertThat(got.get()).isEqualTo("auth-9");
    }

    @Test
    @DisplayName("put() waits while full, and finishes once a consumer makes room")
    void putWaitsWhileFull() throws Exception {
        BoundedBuffer<Integer> buffer = new BoundedBuffer<>(2);
        buffer.put(1);
        buffer.put(2);
        AtomicBoolean third = new AtomicBoolean();
        Thread producer = daemon(() -> {
            try { buffer.put(3); third.set(true); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        assertThat(reachesWaiting(producer)).as("producer parked in wait()").isTrue();
        assertThat(third.get()).isFalse();
        assertThat(buffer.take()).isEqualTo(1);
        producer.join(5_000);
        assertThat(third.get()).isTrue();
        assertThat(buffer.size()).isEqualTo(2);
    }

    @Test
    @DisplayName("4 producers and 4 consumers move 100,000 items through 8 slots, each item exactly once")
    void manyProducersAndConsumers() {
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> {
            BoundedBuffer<Integer> buffer = new BoundedBuffer<>(8);
            int producers = 4, consumers = 4, perProducer = 25_000, total = producers * perProducer;
            AtomicIntegerArray seen = new AtomicIntegerArray(total);
            List<Thread> threads = new ArrayList<>();
            for (int p = 0; p < producers; p++) {
                int base = p * perProducer;
                threads.add(daemon(() -> {
                    try { for (int i = 0; i < perProducer; i++) buffer.put(base + i); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                }));
            }
            for (int c = 0; c < consumers; c++) {
                threads.add(daemon(() -> {
                    try { for (int i = 0; i < total / consumers; i++) seen.incrementAndGet(buffer.take()); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                }));
            }
            for (Thread t : threads) t.join();
            for (int i = 0; i < total; i++) assertThat(seen.get(i)).as("times item %d was taken", i).isEqualTo(1);
            assertThat(buffer.size()).isZero();
        });
    }

    @Test
    @DisplayName("a waiting take() gives up with InterruptedException when its thread is interrupted")
    void takeIsInterruptible() throws Exception {
        BoundedBuffer<String> buffer = new BoundedBuffer<>(1);
        AtomicReference<Throwable> thrown = new AtomicReference<>();
        Thread consumer = daemon(() -> {
            try { buffer.take(); } catch (Throwable e) { thrown.set(e); }
        });
        assertThat(reachesWaiting(consumer)).isTrue();
        consumer.interrupt();
        consumer.join(5_000);
        assertThat(thrown.get()).isInstanceOf(InterruptedException.class);
    }

    @Test
    @DisplayName("rejects a capacity below 1")
    void rejectsBadCapacity() {
        assertThatThrownBy(() -> new BoundedBuffer<String>(0)).isInstanceOf(IllegalArgumentException.class);
    }
}
