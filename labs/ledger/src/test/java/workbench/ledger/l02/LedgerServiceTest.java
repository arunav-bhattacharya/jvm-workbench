package workbench.ledger.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LedgerServiceTest {

    static Map<String, Long> accounts(int n, long each) {
        Map<String, Long> m = new TreeMap<>();
        for (int i = 0; i < n; i++) m.put(String.format("acc-%02d", i), each);
        return m;
    }

    static Transfer randomTransfer(List<String> ids, String id, long maxCents) {
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        int a = rnd.nextInt(ids.size());
        int b = rnd.nextInt(ids.size() - 1);
        if (b >= a) b++;
        return new Transfer(id, ids.get(a), ids.get(b), 1 + rnd.nextLong(maxCents));
    }

    @Test
    @DisplayName("PoolPlan from Little's law: 1,600 a second x 5 ms is 8 threads; 50 ms of waiting is 80 queue slots")
    void poolPlanFromLittlesLaw() {
        assertThat(PoolPlan.fromLittlesLaw(1_600, Duration.ofMillis(5), Duration.ofMillis(50))).isEqualTo(new PoolPlan(8, 80));
        assertThat(PoolPlan.fromLittlesLaw(250, Duration.ofMillis(120), Duration.ofSeconds(1))).isEqualTo(new PoolPlan(30, 250));
        assertThat(PoolPlan.fromLittlesLaw(3, Duration.ofMillis(500), Duration.ofMillis(100))).as("rounds up").isEqualTo(new PoolPlan(2, 1));
        assertThat(PoolPlan.fromLittlesLaw(10, Duration.ofNanos(1), Duration.ofNanos(1))).as("never below 1").isEqualTo(new PoolPlan(1, 1));
    }

    @Test
    @DisplayName("Worker threads are named ledger-0, ledger-1, ...")
    void namedThreads() throws Exception {
        Set<String> names = ConcurrentHashMap.newKeySet();
        LedgerService service = LedgerService.start(new Ledger(accounts(4, 1_000)),
                t -> names.add(Thread.currentThread().getName()), new PoolPlan(3, 100));
        try {
            List<Future<Outcome>> fs = new ArrayList<>();
            for (int i = 0; i < 60; i++) fs.add(service.submit(new Transfer("t" + i, "acc-00", "acc-01", 1)));
            for (Future<Outcome> f : fs) assertThat(f.get(5, TimeUnit.SECONDS)).isEqualTo(Outcome.APPLIED);
        } finally {
            service.shutdown(Duration.ofSeconds(5));
        }
        assertThat(names).isNotEmpty().allMatch(n -> n.matches("ledger-[0-2]"), "named ledger-0 to ledger-2");
    }

    @Test
    @DisplayName("A full pool rejects the next transfer and counts the rejection")
    void fullPoolRejectsAndCounts() throws Exception {
        CountDownLatch entered = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        LedgerService service = LedgerService.start(new Ledger(Map.of("alice", 1_000L, "bob", 0L)), t -> {
            entered.countDown();
            release.await();                                  // holds the only thread
        }, new PoolPlan(1, 1));
        try {
            Future<Outcome> running = service.submit(new Transfer("t1", "alice", "bob", 10));
            assertThat(entered.await(5, TimeUnit.SECONDS)).as("the first transfer started").isTrue();
            Future<Outcome> queued = service.submit(new Transfer("t2", "alice", "bob", 10));   // fills the one queue slot
            assertThatThrownBy(() -> service.submit(new Transfer("t3", "alice", "bob", 10)))
                    .isInstanceOf(RejectedExecutionException.class);
            assertThat(service.rejected()).isEqualTo(1);
            release.countDown();
            assertThat(running.get(5, TimeUnit.SECONDS)).isEqualTo(Outcome.APPLIED);
            assertThat(queued.get(5, TimeUnit.SECONDS)).isEqualTo(Outcome.APPLIED);
        } finally {
            release.countDown();
            service.shutdown(Duration.ofSeconds(5));
        }
        assertThat(service.ledger().balanceOf("bob")).isEqualTo(20);
    }

    @Test
    @DisplayName("A graceful shutdown applies every accepted transfer: 4 submitters x 5,000, none lost")
    void gracefulShutdownLosesNothing() throws Exception {
        Ledger ledger = new Ledger(accounts(20, 10_000));                       // 200,000 cents
        AtomicInteger journaled = new AtomicInteger();
        LedgerService service = LedgerService.start(ledger, t -> {
            journaled.incrementAndGet();
            for (int i = 0; i < 50; i++) Thread.onSpinWait();                   // a little work per transfer
        }, new PoolPlan(4, 50_000));
        List<Future<Outcome>> futures = new CopyOnWriteArrayList<>();
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> submitters = new ArrayList<>();
        for (int s = 0; s < 4; s++) {
            int me = s;
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                List<Future<Outcome>> mine = new ArrayList<>();
                for (int n = 0; n < 5_000; n++) mine.add(service.submit(randomTransfer(ledger.accountIds(), "s" + me + "-" + n, 3_000)));
                futures.addAll(mine);
            });
            t.start();
            submitters.add(t);
        }
        go.countDown();
        for (Thread t : submitters) t.join();
        LedgerService.ShutdownReport report = service.shutdown(Duration.ofSeconds(30));   // straight after the last submit

        assertThat(report.drained()).as("the queue drained inside the grace period").isTrue();
        assertThat(report.neverStarted()).isEmpty();
        assertThat(futures).hasSize(20_000);
        int applied = 0, refused = 0;
        for (Future<Outcome> f : futures) {
            assertThat(f.isDone()).isTrue();
            if (f.get() == Outcome.APPLIED) applied++; else refused++;
        }
        assertThat(applied + refused).isEqualTo(20_000);
        assertThat(journaled.get()).as("every accepted transfer was journaled").isEqualTo(20_000);
        assertThat(service.rejected()).isZero();
        BalanceSnapshot end = ledger.snapshot();
        assertThat(end.total()).isEqualTo(200_000);
        assertThat(end.sum()).isEqualTo(200_000);
    }

    @Test
    @DisplayName("A shutdown that runs out of time interrupts the running transfer and hands back the queued ones")
    void shutdownHandsBackWhatNeverRan() throws Exception {
        Ledger ledger = new Ledger(Map.of("alice", 1_000L, "bob", 0L));
        CountDownLatch entered = new CountDownLatch(1);
        CountDownLatch never = new CountDownLatch(1);
        AtomicBoolean interrupted = new AtomicBoolean();
        LedgerService service = LedgerService.start(ledger, t -> {
            entered.countDown();
            try {
                never.await();                                // a journal write that never finishes
            } catch (InterruptedException e) {
                interrupted.set(true);
                throw e;
            }
        }, new PoolPlan(1, 10));
        List<Future<Outcome>> fs = new ArrayList<>();
        for (int i = 1; i <= 5; i++) fs.add(service.submit(new Transfer("t" + i, "alice", "bob", 100)));
        assertThat(entered.await(5, TimeUnit.SECONDS)).as("t1 started").isTrue();

        LedgerService.ShutdownReport report = service.shutdown(Duration.ofMillis(200));

        assertThat(report.drained()).isFalse();
        assertThat(report.neverStarted()).extracting(Transfer::id).containsExactly("t2", "t3", "t4", "t5");
        for (Future<Outcome> f : fs.subList(1, 5)) assertThat(f.isCancelled()).as("a waiting caller is woken").isTrue();
        assertThat(interrupted.get()).as("t1's journal write was interrupted").isTrue();
        assertThatThrownBy(() -> fs.get(0).get(5, TimeUnit.SECONDS))
                .isInstanceOf(ExecutionException.class).hasCauseInstanceOf(InterruptedException.class);
        assertThat(ledger.balanceOf("alice")).as("nothing half-applied").isEqualTo(1_000);
        assertThat(ledger.balanceOf("bob")).isZero();
    }

    @Test
    @DisplayName("A transfer submitted after shutdown is rejected and counted")
    void submitAfterShutdown() throws Exception {
        LedgerService service = LedgerService.start(new Ledger(Map.of("alice", 100L, "bob", 0L)), Journal.NONE, new PoolPlan(2, 10));
        assertThat(service.shutdown(Duration.ofSeconds(5)).drained()).isTrue();
        assertThatThrownBy(() -> service.submit(new Transfer("late", "alice", "bob", 1)))
                .isInstanceOf(RejectedExecutionException.class);
        assertThat(service.rejected()).isEqualTo(1);
        assertThat(service.ledger().balanceOf("alice")).isEqualTo(100);
    }

    @Test
    @DisplayName("A snapshot taken while 4 threads move money always adds up, and versions only go forward")
    void snapshotNeverTorn() throws Exception {
        Ledger ledger = new Ledger(accounts(50, 1_000));                       // 50,000 cents
        AtomicBoolean writing = new AtomicBoolean(true);
        AtomicLong taken = new AtomicLong(), torn = new AtomicLong(), backwards = new AtomicLong(), lastVersion = new AtomicLong();
        CountDownLatch go = new CountDownLatch(1);
        Thread reader = new Thread(() -> {
            try { go.await(); } catch (InterruptedException e) { return; }
            long last = -1;
            do {
                BalanceSnapshot s = ledger.snapshot();
                taken.incrementAndGet();
                if (s.sum() != 50_000 || s.total() != 50_000) torn.incrementAndGet();
                if (s.version() <= last) backwards.incrementAndGet();
                last = s.version();
            } while (writing.get());
            lastVersion.set(last);
        });
        reader.start();
        List<Thread> writers = new ArrayList<>();
        for (int w = 0; w < 4; w++) {
            int me = w;
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                for (int n = 0; n < 50_000; n++) ledger.apply(randomTransfer(ledger.accountIds(), "w" + me + "-" + n, 500));
            });
            t.start();
            writers.add(t);
        }
        go.countDown();
        for (Thread t : writers) t.join();
        writing.set(false);
        reader.join();

        assertThat(taken.get()).as("snapshots taken during the run").isGreaterThanOrEqualTo(10);
        assertThat(torn.get()).as("snapshots whose balances did not add up to 50,000").isZero();
        assertThat(backwards.get()).as("versions that went backwards").isZero();
        assertThat(ledger.latestSnapshot().version()).isEqualTo(lastVersion.get());
    }

    @Test
    @DisplayName("A snapshot is immutable, and latestSnapshot returns the newest one without locking")
    void snapshotIsImmutableAndPublished() {
        Ledger ledger = new Ledger(Map.of("alice", 100L, "bob", 0L));
        BalanceSnapshot opening = ledger.latestSnapshot();
        assertThat(opening.version()).isZero();
        BalanceSnapshot s1 = ledger.snapshot();
        assertThat(ledger.latestSnapshot()).isSameAs(s1);
        assertThat(s1.version()).isGreaterThan(opening.version());
        assertThatThrownBy(() -> s1.balances().put("bob", 1_000_000L)).isInstanceOf(UnsupportedOperationException.class);

        ledger.apply(new Transfer("t1", "alice", "bob", 40));
        assertThat(ledger.latestSnapshot()).as("published only when someone takes a snapshot").isSameAs(s1);
        BalanceSnapshot s2 = ledger.snapshot();
        assertThat(s2.balances()).containsEntry("alice", 60L).containsEntry("bob", 40L);
        assertThat(s2.version()).isGreaterThan(s1.version());
        assertThat(s1.balances()).as("an old snapshot never changes").containsEntry("alice", 100L);
    }
}
