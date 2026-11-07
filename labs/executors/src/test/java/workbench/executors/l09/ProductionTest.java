package workbench.executors.l09;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class ProductionTest {
    record Failure(String requestId, String threadName, Throwable error) {}

    /** Records every report and lets a test wait for the first one. */
    static final class RecordingLog implements FailureLog {
        final List<Failure> failures = new CopyOnWriteArrayList<>();
        final CountDownLatch first = new CountDownLatch(1);

        @Override
        public void failed(String requestId, String threadName, Throwable error) {
            failures.add(new Failure(requestId, threadName, error));
            first.countDown();
        }

        Failure awaitFirst() throws InterruptedException {
            assertThat(first.await(5, TimeUnit.SECONDS)).as("a failure was reported").isTrue();
            return failures.get(0);
        }
    }

    private final RecordingLog log = new RecordingLog();
    private final List<ExecutorService> pools = new ArrayList<>();

    private <T extends ExecutorService> T track(T pool) {
        pools.add(pool);
        return pool;
    }

    @AfterEach
    void stop() {
        RequestContext.clear();
        pools.forEach(ExecutorService::shutdownNow);
    }

    @Test
    @DisplayName("ProductionPool names its threads name-0, name-1, ...")
    void namesThreads() throws Exception {
        ProductionPool pool = track(ProductionPool.create("ledger", 2, 10, log));
        CyclicBarrier both = new CyclicBarrier(2);
        Set<String> names = ConcurrentHashMap.newKeySet();
        Runnable task = () -> {
            names.add(Thread.currentThread().getName());
            try {
                both.await(5, TimeUnit.SECONDS);            // keeps the first thread busy so the second one starts
            } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                throw new IllegalStateException(e);
            }
        };
        Future<?> a = pool.submit(task);
        Future<?> b = pool.submit(task);
        a.get(5, TimeUnit.SECONDS);
        b.get(5, TimeUnit.SECONDS);
        assertThat(names).containsExactlyInAnyOrder("ledger-0", "ledger-1");
    }

    @Test
    @DisplayName("ProductionPool rejects work when its bounded queue is full")
    void rejectsWhenFull() {
        ProductionPool pool = track(ProductionPool.create("ledger", 1, 1, log));
        CountDownLatch release = new CountDownLatch(1);
        Runnable blocked = () -> {
            try {
                release.await();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };
        try {
            pool.execute(blocked);                          // runs
            pool.execute(blocked);                          // waits in the queue of 1
            assertThatThrownBy(() -> pool.execute(blocked)).isInstanceOf(RejectedExecutionException.class);
        } finally {
            release.countDown();
        }
    }

    @Test
    @DisplayName("a task sees the request id of the thread that submitted it")
    void carriesTheRequestId() throws Exception {
        ProductionPool pool = track(ProductionPool.create("ledger", 2, 10, log));
        RequestContext.set("req-42");
        assertThat(pool.submit(RequestContext::get).get(5, TimeUnit.SECONDS)).isEqualTo("req-42");
        assertThat(log.failures).as("reported failures").isEmpty();
    }

    @Test
    @DisplayName("a request id never leaks into the next task on the same thread")
    void doesNotLeak() throws Exception {
        ProductionPool pool = track(ProductionPool.create("ledger", 1, 10, log));
        RequestContext.set("req-1");
        assertThat(pool.submit(RequestContext::get).get(5, TimeUnit.SECONDS)).isEqualTo("req-1");

        RequestContext.clear();                              // the next caller has no request id
        assertThat(pool.submit(RequestContext::get).get(5, TimeUnit.SECONDS)).as("seen by the next task").isNull();
    }

    @Test
    @DisplayName("a failure in execute() is reported with the request id, the thread and the exception, and the worker survives")
    void reportsExecuteFailures() throws Exception {
        ProductionPool pool = track(ProductionPool.create("ledger", 1, 10, log));
        IllegalStateException boom = new IllegalStateException("ledger row locked");
        RequestContext.set("req-7");
        pool.execute(() -> { throw boom; });

        Failure f = log.awaitFirst();
        assertThat(f.requestId()).isEqualTo("req-7");
        assertThat(f.threadName()).isEqualTo("ledger-0");
        assertThat(f.error()).isSameAs(boom);

        // the same worker runs the next task: the failure didn't kill it
        assertThat(pool.submit(() -> Thread.currentThread().getName()).get(5, TimeUnit.SECONDS)).isEqualTo("ledger-0");
        assertThat(log.failures).as("reported exactly once").hasSize(1);
    }

    @Test
    @DisplayName("a failure in submit() is reported too, and the Future still fails with it")
    void reportsSubmitFailures() throws Exception {
        ProductionPool pool = track(ProductionPool.create("ledger", 1, 10, log));
        IllegalArgumentException bad = new IllegalArgumentException("negative amount");
        RequestContext.set("req-8");
        Future<String> f = pool.submit(() -> { throw bad; });

        assertThatThrownBy(() -> f.get(5, TimeUnit.SECONDS)).isInstanceOf(ExecutionException.class).hasCause(bad);
        Failure reported = log.awaitFirst();
        assertThat(reported.requestId()).isEqualTo("req-8");
        assertThat(reported.error()).as("the original exception, not a wrapper").isSameAs(bad);
    }

    private static final LedgerClient LEDGER = merchant -> List.of(merchant + "-a", merchant + "-b", merchant + "-c");

    @Test
    @DisplayName("StatementJob finishes 6 merchants on a 2-thread pool, in merchant order")
    void statementsOnTwoThreads() {
        ExecutorService pool = track(Executors.newFixedThreadPool(2));
        StatementJob job = new StatementJob(pool, LEDGER);
        List<String> merchants = List.of("m1", "m2", "m3", "m4", "m5", "m6");

        List<String> statements = assertTimeoutPreemptively(Duration.ofSeconds(5), () -> job.run(merchants),
                "the job hung: pool threads are waiting for tasks queued behind them");
        assertThat(statements).containsExactly(
                "m1: 3 lines", "m2: 3 lines", "m3: 3 lines", "m4: 3 lines", "m5: 3 lines", "m6: 3 lines");
    }

    @Test
    @DisplayName("StatementJob finishes even on a 1-thread pool")
    void statementsOnOneThread() {
        ExecutorService pool = track(Executors.newFixedThreadPool(1));
        StatementJob job = new StatementJob(pool, LEDGER);
        List<String> statements = assertTimeoutPreemptively(Duration.ofSeconds(5), () -> job.run(List.of("solo", "duo")),
                "the job hung: pool threads are waiting for tasks queued behind them");
        assertThat(statements).containsExactly("solo: 3 lines", "duo: 3 lines");
    }
}
