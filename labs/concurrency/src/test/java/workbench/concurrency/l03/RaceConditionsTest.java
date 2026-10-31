package workbench.concurrency.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Set;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class RaceConditionsTest {
    private static final int THREADS = 8;

    // the tests use their own harness, so a bug in your Hammer doesn't hide the other results
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
    @DisplayName("Hammer runs the task once per thread, on different threads")
    void hammerRunsEveryThread() throws Exception {
        AtomicInteger runs = new AtomicInteger();
        Set<String> names = ConcurrentHashMap.newKeySet();
        Hammer.run(THREADS, () -> { runs.incrementAndGet(); names.add(Thread.currentThread().getName()); });
        assertThat(runs.get()).isEqualTo(THREADS);
        assertThat(names).hasSize(THREADS);
    }

    @Test
    @DisplayName("Hammer releases the threads together, so they overlap")
    void hammerThreadsOverlap() throws Exception {
        // every task waits at a barrier for all the others; this only completes if they run at the same time
        CyclicBarrier allHere = new CyclicBarrier(THREADS);
        AtomicInteger met = new AtomicInteger();
        Hammer.run(THREADS, () -> {
            try {
                allHere.await(3, TimeUnit.SECONDS);
                met.incrementAndGet();
            } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                // a thread that never met the others leaves met short
            }
        });
        assertThat(met.get()).isEqualTo(THREADS);
    }

    @Test
    @DisplayName("Hammer returns only after every thread has finished")
    void hammerJoins() throws Exception {
        AtomicInteger finished = new AtomicInteger();
        Hammer.run(4, () -> {
            try { Thread.sleep(50); } catch (InterruptedException e) { return; }
            finished.incrementAndGet();
        });
        assertThat(finished.get()).isEqualTo(4);
    }

    @Test
    @DisplayName("HitCounter counts every hit from 8 threads x 200,000 hits")
    void counterLosesNothing() throws Exception {
        HitCounter counter = new HitCounter();
        collide(THREADS, () -> { for (int i = 0; i < 200_000; i++) counter.hit(); });
        assertThat(counter.total()).isEqualTo(THREADS * 200_000);
    }

    @Test
    @DisplayName("SeatMap sells each seat exactly once when 8 buyers race for 2,000 seats")
    void noDoubleBooking() throws Exception {
        SeatMap map = new SeatMap();
        int seats = 2_000;
        AtomicInteger sold = new AtomicInteger();
        ConcurrentHashMap<Integer, String> winners = new ConcurrentHashMap<>();
        AtomicInteger ids = new AtomicInteger();
        collide(THREADS, () -> {
            String me = "buyer-" + ids.incrementAndGet();
            for (int s = 0; s < seats; s++) {
                if (map.book(s, me)) {
                    sold.incrementAndGet();
                    winners.put(s, me);
                }
            }
        });
        assertThat(sold.get()).as("seats sold").isEqualTo(seats);
        for (int s = 0; s < seats; s++) {
            assertThat(map.ownerOf(s)).as("owner of seat " + s).isEqualTo(winners.get(s));
        }
    }
}
