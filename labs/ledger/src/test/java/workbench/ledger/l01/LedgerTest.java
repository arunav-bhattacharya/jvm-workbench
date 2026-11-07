package workbench.ledger.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;
import static workbench.ledger.l01.Outcome.APPLIED;
import static workbench.ledger.l01.Outcome.INSUFFICIENT_FUNDS;

class LedgerTest {

    static Map<String, Long> accounts(int n, long each) {
        Map<String, Long> m = new TreeMap<>();
        for (int i = 0; i < n; i++) m.put(String.format("acc-%02d", i), each);
        return m;
    }

    @Test
    @DisplayName("A Transfer refuses a missing id or account, a zero or negative amount, and a transfer to itself")
    void transferIsAlwaysValid() {
        assertThatThrownBy(() -> new Transfer(null, "alice", "bob", 10)).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> new Transfer("t1", null, "bob", 10)).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> new Transfer("t1", "alice", null, 10)).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> new Transfer("t1", "alice", "bob", 0)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Transfer("t1", "alice", "bob", -5)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Transfer("t1", "alice", "alice", 10)).isInstanceOf(IllegalArgumentException.class);
        assertThat(new Transfer("t1", "alice", "bob", 10).cents()).isEqualTo(10);
    }

    @Test
    @DisplayName("apply moves the money, and refuses a transfer that would overdraw")
    void applyMovesAndRefuses() {
        Ledger ledger = new Ledger(Map.of("alice", 100L, "bob", 0L));
        assertThat(ledger.apply(new Transfer("t1", "alice", "bob", 60))).isEqualTo(APPLIED);
        assertThat(ledger.apply(new Transfer("t2", "alice", "bob", 60))).isEqualTo(INSUFFICIENT_FUNDS);
        assertThat(ledger.balanceOf("alice")).isEqualTo(40);
        assertThat(ledger.balanceOf("bob")).isEqualTo(60);
        assertThat(ledger.apply(new Transfer("t3", "alice", "bob", 40))).as("down to exactly zero").isEqualTo(APPLIED);
        assertThat(ledger.balanceOf("alice")).isZero();
        assertThat(ledger.apply(new Transfer("t4", "bob", "alice", 100))).as("the other direction").isEqualTo(APPLIED);
        assertThat(ledger.total()).isEqualTo(100);
    }

    @Test
    @DisplayName("apply rejects an unknown account and changes nothing")
    void unknownAccount() {
        Ledger ledger = new Ledger(Map.of("alice", 100L, "bob", 0L));
        assertThatThrownBy(() -> ledger.apply(new Transfer("t1", "alice", "mallory", 1)))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> ledger.apply(new Transfer("t2", "mallory", "bob", 1)))
                .isInstanceOf(IllegalArgumentException.class);
        assertThat(ledger.balanceOf("alice")).isEqualTo(100);
        assertThat(ledger.balanceOf("bob")).isZero();
    }

    @Test
    @DisplayName("apply releases both locks on every path, including a refusal")
    void releasesLocks() {
        Ledger ledger = new Ledger(Map.of("alice", 10L, "bob", 0L));
        assertThat(ledger.apply(new Transfer("t1", "alice", "bob", 50))).isEqualTo(INSUFFICIENT_FUNDS);
        assertThat(ledger.apply(new Transfer("t2", "alice", "bob", 5))).isEqualTo(APPLIED);
        // another thread can only get in if this thread let go of both locks
        assertTimeoutPreemptively(Duration.ofSeconds(5), () -> {
            AtomicReference<Outcome> seen = new AtomicReference<>();
            Thread other = new Thread(() -> seen.set(ledger.apply(new Transfer("t3", "bob", "alice", 5))));
            other.setDaemon(true);
            other.start();
            other.join();
            assertThat(seen.get()).isEqualTo(APPLIED);
        }, "another thread could not take the locks: apply left one locked");
    }

    @Test
    @DisplayName("Opposite transfers between the same two accounts never deadlock (2 threads x 100,000)")
    void oppositeTransfersNeverDeadlock() {
        Ledger ledger = new Ledger(Map.of("acc-a", 1_000L, "acc-b", 1_000L));
        AtomicInteger done = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> {
            CountDownLatch go = new CountDownLatch(1);
            Thread ab = worker(go, () -> {
                for (int i = 0; i < 100_000; i++) { ledger.apply(new Transfer("ab" + i, "acc-a", "acc-b", 1)); done.incrementAndGet(); }
            });
            Thread ba = worker(go, () -> {
                for (int i = 0; i < 100_000; i++) { ledger.apply(new Transfer("ba" + i, "acc-b", "acc-a", 1)); done.incrementAndGet(); }
            });
            go.countDown();
            ab.join();
            ba.join();
        }, "the two transfer threads deadlocked: lock the lower account id first");
        assertThat(done.get()).as("transfers that returned").isEqualTo(200_000);
        assertThat(ledger.total()).isEqualTo(2_000);
    }

    @Test
    @DisplayName("StressHarness runs every transfer exactly once, on as many threads as you asked for")
    void harnessRunsEverything() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        Set<String> threadNames = ConcurrentHashMap.newKeySet();
        StressHarness.Result r = StressHarness.run(6, 1_000, List.of("a", "b", "c"), 100, t -> {
            threadNames.add(Thread.currentThread().getName());
            return calls.incrementAndGet() % 3 == 0 ? INSUFFICIENT_FUNDS : APPLIED;
        });
        assertThat(calls.get()).isEqualTo(6_000);
        assertThat(r.total()).isEqualTo(6_000);
        assertThat(r.refused()).isEqualTo(2_000);
        assertThat(threadNames).hasSize(6).doesNotContain(Thread.currentThread().getName());
    }

    @Test
    @DisplayName("StressHarness releases its threads together, so they overlap")
    void harnessThreadsOverlap() throws Exception {
        int threads = 8;
        CyclicBarrier allHere = new CyclicBarrier(threads);
        Set<String> firstCallDone = ConcurrentHashMap.newKeySet();
        AtomicInteger met = new AtomicInteger();
        StressHarness.run(threads, 10, List.of("a", "b"), 10, t -> {
            // the first call on each thread waits for all the others: this only works if they run at the same time
            if (firstCallDone.add(Thread.currentThread().getName())) {
                try {
                    allHere.await(5, TimeUnit.SECONDS);
                    met.incrementAndGet();
                } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                    // a thread that never met the others leaves met short
                }
            }
            return APPLIED;
        });
        assertThat(met.get()).isEqualTo(threads);
    }

    @Test
    @DisplayName("StressHarness makes valid random transfers between the accounts it was given")
    void harnessMakesValidTransfers() throws Exception {
        List<String> ids = List.of("acc-00", "acc-01", "acc-02", "acc-03");
        Set<String> transferIds = ConcurrentHashMap.newKeySet();
        Set<String> pairs = ConcurrentHashMap.newKeySet();
        AtomicInteger bad = new AtomicInteger();
        StressHarness.run(4, 2_000, ids, 50, t -> {
            if (!ids.contains(t.from()) || !ids.contains(t.to()) || t.from().equals(t.to())
                    || t.cents() < 1 || t.cents() > 50 || !transferIds.add(t.id())) {
                bad.incrementAndGet();
            }
            pairs.add(t.from() + ">" + t.to());
            return APPLIED;
        });
        assertThat(bad.get()).as("transfers with a bad account, amount or a repeated id").isZero();
        assertThat(pairs).as("random pairs cover every direction").hasSize(12);
    }

    @Test
    @DisplayName("8 threads x 100,000 random transfers: money is conserved and no balance goes negative")
    void invariantsUnderStress() throws Exception {
        Ledger ledger = new Ledger(accounts(50, 10_000));                 // 500,000 cents in total
        StressHarness.Result r = StressHarness.run(8, 100_000, ledger.accountIds(), 5_000, ledger::apply);
        assertThat(r.total()).as("every transfer was applied or refused").isEqualTo(800_000);
        assertThat(ledger.total()).as("invariant 1: money is conserved").isEqualTo(500_000);
        for (String id : ledger.accountIds()) {
            assertThat(ledger.balanceOf(id)).as("invariant 2: balance of " + id).isNotNegative();
        }
        assertThat(r.applied()).as("transfers applied").isPositive();
        assertThat(r.refused()).as("refusals prove the overdraft check ran").isPositive();
    }

    private static Thread worker(CountDownLatch go, Runnable body) {
        Thread t = new Thread(() -> {
            try {
                go.await();
            } catch (InterruptedException e) {
                return;
            }
            body.run();
        });
        t.setDaemon(true);   // a deadlocked worker must not keep the test JVM alive
        t.start();
        return t;
    }
}
