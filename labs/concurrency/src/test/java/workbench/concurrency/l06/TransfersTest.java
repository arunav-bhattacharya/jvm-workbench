package workbench.concurrency.l06;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class TransfersTest {

    /** Starts daemon threads released by one latch, and joins them. Daemon, so a deadlocked stub can't keep the JVM alive. */
    private static void race(List<Runnable> tasks) throws InterruptedException {
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

    private static long total(Account... accounts) {
        long sum = 0;
        for (Account a : accounts) sum += a.balanceCents();
        return sum;
    }

    @Test
    @DisplayName("transfer: two threads moving money in opposite directions both finish")
    void oppositeDirections() {
        Account a = new Account(1, 1_000_000), b = new Account(2, 1_000_000);
        assertTimeoutPreemptively(Duration.ofSeconds(10), () -> race(List.of(
                () -> { for (int i = 0; i < 50_000; i++) Transfers.transfer(a, b, 1); },
                () -> { for (int i = 0; i < 50_000; i++) Transfers.transfer(b, a, 1); })),
                "deadlocked: the threads took the two locks in opposite orders");
        assertThat(total(a, b)).isEqualTo(2_000_000);
    }

    @Test
    @DisplayName("transfer: 8 threads moving money at random among 5 accounts never deadlock, and no cent is lost")
    void randomTransfers() {
        Account[] accounts = new Account[5];
        for (int i = 0; i < accounts.length; i++) accounts[i] = new Account(i + 10, 100_000);
        List<Runnable> tasks = new ArrayList<>();
        for (int t = 0; t < 8; t++) {
            long seed = t;
            tasks.add(() -> {
                Random random = new Random(seed);
                for (int i = 0; i < 20_000; i++) {
                    Account from = accounts[random.nextInt(accounts.length)];
                    Account to = accounts[random.nextInt(accounts.length)];
                    Transfers.transfer(from, to, 1 + random.nextInt(50));
                }
            });
        }
        assertTimeoutPreemptively(Duration.ofSeconds(10), () -> race(tasks), "deadlocked");
        assertThat(total(accounts)).isEqualTo(500_000);
    }

    @Test
    @DisplayName("tryTransfer: moves the money and returns true when nobody else holds the locks")
    void tryTransferWhenFree() throws Exception {
        Account a = new Account(1, 500), b = new Account(2, 0);
        assertThat(Transfers.tryTransfer(a, b, 200, Duration.ofSeconds(1))).isTrue();
        assertThat(a.balanceCents()).isEqualTo(300);
        assertThat(b.balanceCents()).isEqualTo(200);
    }

    @Test
    @DisplayName("tryTransfer: gives up when another thread holds `to`, changes nothing, and holds no lock afterwards")
    void tryTransferGivesUp() throws Exception {
        Account a = new Account(1, 500), b = new Account(2, 0);
        CountDownLatch held = new CountDownLatch(1), release = new CountDownLatch(1);
        Thread holder = new Thread(() -> {
            b.lock().lock();
            try {
                held.countDown();
                release.await(10, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                b.lock().unlock();
            }
        });
        holder.setDaemon(true);
        holder.start();
        assertThat(held.await(5, TimeUnit.SECONDS)).isTrue();
        try {
            boolean moved = assertTimeoutPreemptively(Duration.ofSeconds(5),
                    () -> Transfers.tryTransfer(a, b, 200, Duration.ofMillis(300)));
            assertThat(moved).as("returned true while `to` was locked by another thread").isFalse();
            assertThat(a.lock().isLocked()).as("`from` still locked after tryTransfer returned").isFalse();
        } finally {
            release.countDown();
        }
        holder.join(5_000);
        assertThat(a.balanceCents()).isEqualTo(500);
        assertThat(b.balanceCents()).isZero();
    }

    @Test
    @DisplayName("tryTransfer: opposite directions on the same two accounts keep making progress")
    void tryTransferMakesProgress() {
        Account a = new Account(1, 1_000_000), b = new Account(2, 1_000_000);
        AtomicInteger moved = new AtomicInteger();
        Runnable ab = () -> {
            for (int i = 0; i < 2_000; i++) {
                try {
                    if (Transfers.tryTransfer(a, b, 1, Duration.ofSeconds(2))) moved.incrementAndGet();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        };
        Runnable ba = () -> {
            for (int i = 0; i < 2_000; i++) {
                try {
                    if (Transfers.tryTransfer(b, a, 1, Duration.ofSeconds(2))) moved.incrementAndGet();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        };
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> race(List.of(ab, ba)));
        assertThat(moved.get()).as("transfers that succeeded").isEqualTo(4_000);
        assertThat(total(a, b)).isEqualTo(2_000_000);
    }
}
