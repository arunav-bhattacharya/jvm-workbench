package workbench.patterns.l11;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l11.Bulkhead.BulkheadFull;
import workbench.patterns.l11.CircuitBreaker.CallNotPermitted;
import workbench.patterns.l11.CircuitBreaker.Closed;
import workbench.patterns.l11.CircuitBreaker.HalfOpen;
import workbench.patterns.l11.CircuitBreaker.Open;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ResilienceTest {

    /** A clock the test moves by hand: no sleeping, no flaky timing. */
    static final class TestClock extends Clock {
        private Instant now = Instant.ofEpochSecond(1_700_000_000L);
        void advance(Duration d) { now = now.plus(d); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { return this; }
        @Override public Instant instant() { return now; }
    }

    private final TestClock clock = new TestClock();
    private final CircuitBreaker breaker = new CircuitBreaker(3, Duration.ofSeconds(30), clock);
    private final AtomicInteger calls = new AtomicInteger();
    private final Supplier<String> ok = () -> { calls.incrementAndGet(); return "ok"; };
    private final Supplier<String> failing = () -> { calls.incrementAndGet(); throw new IllegalStateException("PSP 503"); };

    private void failTimes(int n) {
        for (int i = 0; i < n; i++) {
            assertThatThrownBy(() -> breaker.call(failing)).isInstanceOf(IllegalStateException.class);
        }
    }

    // ---- circuit breaker ----

    @Test
    @DisplayName("Starts closed and passes calls through, returning their result")
    void startsClosed() {
        assertThat(breaker.call(ok)).isEqualTo("ok");
        assertThat(breaker.state()).isEqualTo(new Closed(0));
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("Three failures in a row open it, and while open the operation is not even called")
    void opensAfterThreshold() {
        failTimes(2);
        assertThat(breaker.state()).isEqualTo(new Closed(2));
        failTimes(1);
        assertThat(breaker.state()).isEqualTo(new Open(clock.instant().plusSeconds(30)));
        assertThatThrownBy(() -> breaker.call(ok)).isInstanceOf(CallNotPermitted.class);
        assertThat(calls.get()).as("calls that reached the operation").isEqualTo(3);
    }

    @Test
    @DisplayName("The operation's own exception reaches the caller unchanged")
    void rethrowsTheSameException() {
        IllegalStateException boom = new IllegalStateException("issuer timeout");
        assertThatThrownBy(() -> breaker.call(() -> { throw boom; })).isSameAs(boom);
    }

    @Test
    @DisplayName("A success resets the count of consecutive failures")
    void successResets() {
        failTimes(2);
        breaker.call(ok);
        failTimes(2);
        assertThat(breaker.state()).isEqualTo(new Closed(2));
    }

    @Test
    @DisplayName("After the open period, one probe goes through, and its success closes the breaker")
    void probeSuccessCloses() {
        failTimes(3);
        clock.advance(Duration.ofSeconds(29));
        assertThatThrownBy(() -> breaker.call(ok)).as("still open at 29 s").isInstanceOf(CallNotPermitted.class);
        clock.advance(Duration.ofSeconds(2));
        assertThat(breaker.call(ok)).isEqualTo("ok");
        assertThat(breaker.state()).isEqualTo(new Closed(0));
    }

    @Test
    @DisplayName("A failed probe opens the breaker again for a full period")
    void probeFailureReopens() {
        failTimes(3);
        clock.advance(Duration.ofSeconds(31));
        assertThatThrownBy(() -> breaker.call(failing)).isInstanceOf(IllegalStateException.class);
        assertThat(breaker.state()).isEqualTo(new Open(clock.instant().plusSeconds(30)));
        assertThatThrownBy(() -> breaker.call(ok)).isInstanceOf(CallNotPermitted.class);
        clock.advance(Duration.ofSeconds(31));
        assertThat(breaker.call(ok)).isEqualTo("ok");
    }

    @Test
    @DisplayName("While a probe is in flight, every other call is rejected")
    void oneProbeAtATime() throws Exception {
        failTimes(3);
        clock.advance(Duration.ofSeconds(31));
        CountDownLatch entered = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        ExecutorService probeThread = Executors.newSingleThreadExecutor();
        try {
            CompletableFuture<String> probe = CompletableFuture.supplyAsync(() -> breaker.call(() -> {
                entered.countDown();
                try { release.await(5, TimeUnit.SECONDS); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                return "probe ok";
            }), probeThread);
            assertThat(entered.await(2, TimeUnit.SECONDS)).as("the probe started").isTrue();
            assertThat(breaker.state()).isEqualTo(new HalfOpen());
            assertThatThrownBy(() -> breaker.call(ok)).isInstanceOf(CallNotPermitted.class);
            release.countDown();
            assertThat(probe.get(5, TimeUnit.SECONDS)).isEqualTo("probe ok");
            assertThat(breaker.state()).isEqualTo(new Closed(0));
        } finally {
            release.countDown();
            probeThread.shutdownNow();
        }
    }

    // ---- bulkhead ----

    @Test
    @DisplayName("With two calls in flight, the third is rejected at once, and the permits come back")
    void bulkheadRejectsThird() throws Exception {
        Bulkhead bulkhead = new Bulkhead(2);
        CountDownLatch entered = new CountDownLatch(2);
        CountDownLatch release = new CountDownLatch(1);
        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            List<CompletableFuture<String>> inFlight = new ArrayList<>();
            for (int i = 0; i < 2; i++) {
                inFlight.add(CompletableFuture.supplyAsync(() -> bulkhead.call(() -> {
                    entered.countDown();
                    try { release.await(5, TimeUnit.SECONDS); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    return "done";
                }), pool));
            }
            assertThat(entered.await(2, TimeUnit.SECONDS)).as("both calls are inside").isTrue();
            assertThatThrownBy(() -> bulkhead.call(() -> "third")).isInstanceOf(BulkheadFull.class);
            release.countDown();
            for (CompletableFuture<String> f : inFlight) assertThat(f.get(5, TimeUnit.SECONDS)).isEqualTo("done");
            assertThat(bulkhead.available()).isEqualTo(2);
        } finally {
            release.countDown();
            pool.shutdownNow();
        }
    }

    @Test
    @DisplayName("A call that throws still gives its permit back")
    void permitReturnedOnFailure() {
        Bulkhead bulkhead = new Bulkhead(1);
        assertThatThrownBy(() -> bulkhead.call(() -> { throw new IllegalStateException("PSP 503"); }))
                .isInstanceOf(IllegalStateException.class);
        assertThat(bulkhead.available()).isEqualTo(1);
        assertThat(bulkhead.call(() -> "next")).isEqualTo("next");
    }

    @Test
    @DisplayName("Under load from 16 threads, never more than 4 calls run at once")
    void neverMoreThanLimit() throws Exception {
        Bulkhead bulkhead = new Bulkhead(4);
        AtomicInteger inside = new AtomicInteger();
        AtomicInteger maxInside = new AtomicInteger();
        AtomicInteger succeeded = new AtomicInteger();
        AtomicInteger rejected = new AtomicInteger();
        CountDownLatch go = new CountDownLatch(1);
        Thread[] threads = new Thread[16];
        for (int t = 0; t < threads.length; t++) {
            threads[t] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                for (int i = 0; i < 300; i++) {
                    try {
                        bulkhead.call(() -> {
                            maxInside.accumulateAndGet(inside.incrementAndGet(), Math::max);
                            for (int s = 0; s < 200; s++) Thread.onSpinWait();
                            inside.decrementAndGet();
                            return null;
                        });
                        succeeded.incrementAndGet();
                    } catch (BulkheadFull e) {
                        rejected.incrementAndGet();
                    }
                }
            });
            threads[t].start();
        }
        go.countDown();
        for (Thread t : threads) t.join();
        assertThat(maxInside.get()).as("most calls inside at once").isLessThanOrEqualTo(4);
        assertThat(succeeded.get()).isPositive();
        assertThat(succeeded.get() + rejected.get()).isEqualTo(16 * 300);
        assertThat(bulkhead.available()).isEqualTo(4);
    }
}
