package workbench.concurrency.l08;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicIntegerArray;
import java.util.concurrent.atomic.AtomicLong;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class AtomicsTest {
    private static final int THREADS = 8;

    /** Starts one thread per task behind a start latch, then joins them all. */
    private static void collide(List<Runnable> tasks) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>();
        for (Runnable task : tasks) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                task.run();
            });
            t.setDaemon(true);
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join();
    }

    // ---------- MaxTracker ----------

    @Test
    @DisplayName("MaxTracker: offer() returns the max before the call, and a smaller amount never lowers it")
    void maxSingleThread() {
        MaxTracker t = new MaxTracker();
        assertThat(t.max()).isEqualTo(Long.MIN_VALUE);
        assertThat(t.offer(500)).isEqualTo(Long.MIN_VALUE);
        assertThat(t.offer(200)).isEqualTo(500);
        assertThat(t.offer(900)).isEqualTo(500);
        assertThat(t.max()).isEqualTo(900);
    }

    @Test
    @DisplayName("MaxTracker: no two raises start from the same old max (8 threads x 50,000 rising amounts)")
    void maxRaisesFormOneChain() throws Exception {
        // Every offer gets a new, larger amount from a shared ticket, so most offers raise the max.
        // In a correct tracker each raise replaces a different old max. If two raises report the
        // same old max, both threads read it before either wrote: one of the two updates was lost.
        MaxTracker t = new MaxTracker();
        AtomicLong ticket = new AtomicLong();
        int perThread = 50_000;
        long[][] raisedFrom = new long[THREADS][perThread];
        int[] raises = new int[THREADS];
        List<Runnable> tasks = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            int me = i;
            tasks.add(() -> {
                for (int n = 0; n < perThread; n++) {
                    long amount = ticket.incrementAndGet();
                    long prev = t.offer(amount);
                    if (amount > prev) raisedFrom[me][raises[me]++] = prev;
                }
            });
        }
        collide(tasks);
        long[] all = new long[Arrays.stream(raises).sum()];
        int k = 0;
        for (int i = 0; i < THREADS; i++) {
            System.arraycopy(raisedFrom[i], 0, all, k, raises[i]);
            k += raises[i];
        }
        Arrays.sort(all);
        int duplicates = 0;
        for (int i = 1; i < all.length; i++) if (all[i] == all[i - 1]) duplicates++;
        assertThat(duplicates).as("raises that started from an old max another raise had already replaced").isZero();
        assertThat(t.max()).as("final max").isEqualTo(ticket.get());
    }

    // ---------- TreiberStack ----------

    @Test
    @DisplayName("TreiberStack: last in, first out; pop() on an empty stack returns null; null items are rejected")
    void stackSingleThread() {
        TreiberStack<String> s = new TreiberStack<>();
        assertThat(s.isEmpty()).isTrue();
        assertThat(s.pop()).isNull();
        s.push("auth-1");
        s.push("auth-2");
        s.push("auth-3");
        assertThat(s.isEmpty()).isFalse();
        assertThat(List.of(s.pop(), s.pop(), s.pop())).containsExactly("auth-3", "auth-2", "auth-1");
        assertThat(s.pop()).isNull();
        assertThat(s.isEmpty()).isTrue();
        assertThatThrownBy(() -> s.push(null)).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("TreiberStack: 8 threads push 25,000 items each, then 8 threads pop them: every item comes out exactly once")
    void stackPushThenPop() throws Exception {
        TreiberStack<Integer> s = new TreiberStack<>();
        int perThread = 25_000, total = THREADS * perThread;
        List<Runnable> pushers = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            int base = i * perThread;
            pushers.add(() -> { for (int n = 0; n < perThread; n++) s.push(base + n); });
        }
        collide(pushers);

        AtomicIntegerArray seen = new AtomicIntegerArray(total);
        AtomicInteger popped = new AtomicInteger();
        List<Runnable> poppers = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            poppers.add(() -> {
                Integer x;
                while ((x = s.pop()) != null) { seen.incrementAndGet(x); popped.incrementAndGet(); }
            });
        }
        collide(poppers);
        assertThat(popped.get()).as("items popped").isEqualTo(total);
        for (int i = 0; i < total; i++) assertThat(seen.get(i)).as("times item %d came out", i).isEqualTo(1);
        assertThat(s.isEmpty()).isTrue();
    }

    @Test
    @DisplayName("TreiberStack: 4 pushers and 4 poppers running at the same time lose and duplicate nothing")
    void stackPushAndPopTogether() {
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> {
            TreiberStack<Integer> s = new TreiberStack<>();
            int perPusher = 50_000, total = 4 * perPusher;
            AtomicIntegerArray seen = new AtomicIntegerArray(total);
            AtomicInteger popped = new AtomicInteger();
            List<Runnable> tasks = new ArrayList<>();
            for (int i = 0; i < 4; i++) {
                int base = i * perPusher;
                tasks.add(() -> { for (int n = 0; n < perPusher; n++) s.push(base + n); });
                tasks.add(() -> {
                    while (popped.get() < total) {
                        Integer x = s.pop();
                        if (x == null) { Thread.onSpinWait(); continue; }
                        seen.incrementAndGet(x);
                        popped.incrementAndGet();
                    }
                });
            }
            collide(tasks);
            for (int i = 0; i < total; i++) assertThat(seen.get(i)).as("times item %d came out", i).isEqualTo(1);
        }, "poppers never saw every item: were some pushes lost?");
    }
}
