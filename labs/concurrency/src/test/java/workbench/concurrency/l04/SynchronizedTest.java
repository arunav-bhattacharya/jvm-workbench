package workbench.concurrency.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

class SynchronizedTest {
    private static final int THREADS = 8;

    private static void collide(int threads, Runnable task) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            ts[i] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                task.run();
            });
            ts[i].start();
        }
        go.countDown();
        for (Thread t : ts) t.join();
    }

    @Test
    @DisplayName("DeclineCounter counts 8 threads x 100,000 declines exactly")
    void declinesAddUp() throws Exception {
        DeclineCounter counter = new DeclineCounter();
        collide(THREADS, () -> { for (int i = 0; i < 100_000; i++) counter.recordDecline(); });
        assertThat(counter.total()).isEqualTo(THREADS * 100_000);
    }

    @Test
    @DisplayName("FxRateBoard tells every listener about every rate, and keeps the latest")
    void notifiesEveryone() {
        FxRateBoard board = new FxRateBoard();
        List<String> a = new CopyOnWriteArrayList<>(), b = new CopyOnWriteArrayList<>();
        board.subscribe((pair, rate) -> a.add(pair + "=" + rate));
        board.subscribe((pair, rate) -> b.add(pair + "=" + rate));
        board.publish("EURUSD", new BigDecimal("1.0842"));
        board.publish("GBPUSD", new BigDecimal("1.2710"));
        board.publish("EURUSD", new BigDecimal("1.0851"));
        assertThat(a).containsExactly("EURUSD=1.0842", "GBPUSD=1.2710", "EURUSD=1.0851");
        assertThat(b).isEqualTo(a);
        assertThat(board.rate("EURUSD")).isEqualByComparingTo("1.0851");
    }

    @Test
    @DisplayName("FxRateBoard: a listener can ask another thread to read the board while it is notified")
    void listenerCanUseAnotherThread() throws Exception {
        FxRateBoard board = new FxRateBoard();
        AtomicBoolean helperFinished = new AtomicBoolean();
        AtomicReference<BigDecimal> seen = new AtomicReference<>();
        board.subscribe((pair, rate) -> {
            // e.g. a listener that hands work to a pool thread and waits for it
            Thread helper = new Thread(() -> seen.set(board.rate(pair)));
            helper.setDaemon(true);
            helper.start();
            try {
                helper.join(2_000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            helperFinished.set(!helper.isAlive());
        });
        board.publish("EURUSD", new BigDecimal("1.0842"));
        assertThat(helperFinished.get()).as("helper thread could read the board within 2 s").isTrue();
        assertThat(seen.get()).isEqualByComparingTo("1.0842");
    }

    @Test
    @DisplayName("FxRateBoard: a listener may subscribe another listener while it is being notified")
    void listenerCanSubscribe() {
        FxRateBoard board = new FxRateBoard();
        List<String> late = new CopyOnWriteArrayList<>();
        AtomicBoolean added = new AtomicBoolean();
        board.subscribe((pair, rate) -> {
            if (added.compareAndSet(false, true)) board.subscribe((p, r) -> late.add(p));
        });
        board.publish("EURUSD", new BigDecimal("1.0842"));   // the first listener subscribes the second
        board.publish("GBPUSD", new BigDecimal("1.2710"));   // now both hear it
        assertThat(late).contains("GBPUSD");
    }
}
