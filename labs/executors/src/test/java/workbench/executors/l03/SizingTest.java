package workbench.executors.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.within;

class SizingTest {
    static Duration ms(long n) { return Duration.ofMillis(n); }

    @Test
    @DisplayName("ioBound: 8 cores, 80% target, 180 ms wait, 20 ms compute -> 64 threads")
    void goetzFormula() {
        assertThat(PoolSizing.ioBound(8, 0.8, ms(180), ms(20))).isEqualTo(64);
        assertThat(PoolSizing.ioBound(16, 0.75, ms(95), ms(5))).isEqualTo(240);
        assertThat(PoolSizing.ioBound(2, 0.5, ms(100), ms(100))).isEqualTo(2);
    }

    @Test
    @DisplayName("ioBound: pure CPU work gets one thread per core, and never fewer than 1")
    void cpuBoundAndFloor() {
        assertThat(PoolSizing.ioBound(4, 1.0, Duration.ZERO, ms(10))).isEqualTo(4);
        assertThat(PoolSizing.ioBound(1, 0.1, Duration.ZERO, ms(10))).isEqualTo(1);
        assertThat(PoolSizing.ioBound(3, 0.5, ms(10), ms(30))).as("3 * 0.5 * 1.333 = 2.0").isEqualTo(2);
    }

    @Test
    @DisplayName("inFlight: 400 req/s at 250 ms means 100 requests in flight (Little's law)")
    void littlesLaw() {
        assertThat(PoolSizing.inFlight(400, ms(250))).isCloseTo(100.0, within(1e-9));
        assertThat(PoolSizing.inFlight(2_000, ms(500))).isCloseTo(1_000.0, within(1e-9));
    }

    @Test
    @DisplayName("maxThroughput: 50 threads at 250 ms each top out at 200 req/s")
    void throughputCap() {
        assertThat(PoolSizing.maxThroughput(50, ms(250))).isCloseTo(200.0, within(1e-9));
        assertThat(PoolSizing.maxThroughput(20, ms(5))).isCloseTo(4_000.0, within(1e-6));
    }

    @Test
    @DisplayName("threadsFor: rounds up, and a 20-connection pool caps the answer at 20")
    void downstreamCap() {
        assertThat(PoolSizing.threadsFor(400, ms(250), 500)).isEqualTo(100);
        assertThat(PoolSizing.threadsFor(400, ms(250), 20)).isEqualTo(20);
        assertThat(PoolSizing.threadsFor(30, ms(110), 20)).as("3.3 rounds up to 4").isEqualTo(4);
        assertThat(PoolSizing.threadsFor(10, ms(15), 20)).as("never 0").isEqualTo(1);
    }

    @Test
    @DisplayName("Bulkhead never lets more than maxConcurrent calls in at once")
    void boundsConcurrency() throws Exception {
        Bulkhead issuer = new Bulkhead("issuer", 3, Duration.ofSeconds(10));
        AtomicInteger inside = new AtomicInteger();
        AtomicInteger maxInside = new AtomicInteger();
        AtomicInteger ok = new AtomicInteger();
        List<Thread> threads = new ArrayList<>();
        CountDownLatch go = new CountDownLatch(1);
        for (int t = 0; t < 8; t++) {
            Thread th = new Thread(() -> {
                try {
                    go.await();
                    for (int i = 0; i < 25; i++) {
                        issuer.call(() -> {
                            maxInside.accumulateAndGet(inside.incrementAndGet(), Math::max);
                            Thread.sleep(1);
                            inside.decrementAndGet();
                            return ok.incrementAndGet();
                        });
                    }
                } catch (Exception e) {
                    // a failed call leaves ok short
                }
            });
            th.start();
            threads.add(th);
        }
        go.countDown();
        for (Thread th : threads) th.join(20_000);
        assertThat(ok.get()).as("calls that succeeded").isEqualTo(200);
        assertThat(maxInside.get()).as("most calls inside at once").isBetween(1, 3);
        assertThat(issuer.available()).as("permits after the run").isEqualTo(3);
    }

    @Test
    @DisplayName("Bulkhead with zero wait rejects at once while full, and recovers after")
    void failsFastWhenFull() throws Exception {
        Bulkhead issuer = new Bulkhead("issuer", 2, Duration.ZERO);
        CountDownLatch inside = new CountDownLatch(2);
        CountDownLatch release = new CountDownLatch(1);
        List<Thread> holders = new ArrayList<>();
        for (int i = 0; i < 2; i++) {
            Thread th = new Thread(() -> {
                try {
                    issuer.call(() -> { inside.countDown(); release.await(); return null; });
                } catch (Exception e) {
                    // ignore
                }
            });
            th.start();
            holders.add(th);
        }
        assertThat(inside.await(5, TimeUnit.SECONDS)).as("both holders got in").isTrue();
        assertThat(issuer.available()).isZero();

        assertThatThrownBy(() -> issuer.call(() -> "late"))
                .isInstanceOf(BulkheadFullException.class)
                .hasMessageContaining("issuer");

        release.countDown();
        for (Thread th : holders) th.join(5_000);
        assertThat(issuer.call(() -> "after")).isEqualTo("after");
        assertThat(issuer.available()).isEqualTo(2);
    }

    @Test
    @DisplayName("Bulkhead waits up to maxWait for a permit to come free")
    void waitsForPermit() throws Exception {
        Bulkhead ledger = new Bulkhead("ledger", 1, Duration.ofSeconds(10));
        CountDownLatch holding = new CountDownLatch(1);
        Thread holder = new Thread(() -> {
            try {
                ledger.call(() -> { holding.countDown(); Thread.sleep(200); return null; });
            } catch (Exception e) {
                // ignore
            }
        });
        holder.start();
        assertThat(holding.await(5, TimeUnit.SECONDS)).isTrue();
        assertThat(ledger.call(() -> "posted")).isEqualTo("posted");     // waits about 200 ms, then gets in
        holder.join(5_000);
    }

    @Test
    @DisplayName("Bulkhead gives the permit back when the call throws, and rethrows the same exception")
    void releasesOnFailure() throws Exception {
        Bulkhead issuer = new Bulkhead("issuer", 1, Duration.ZERO);
        IOException boom = new IOException("connection reset by issuer");
        for (int i = 0; i < 5; i++) {
            assertThatThrownBy(() -> issuer.call(() -> { throw boom; })).isSameAs(boom);
        }
        assertThat(issuer.available()).isEqualTo(1);
        assertThat(issuer.call(() -> 42)).isEqualTo(42);
    }
}
