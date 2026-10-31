package workbench.vthreads.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FanOutTest {

    /** A fake card issuer: each call sleeps, and the fake records how many calls are inside it at once. */
    static final class FakeIssuer {
        final Duration latency;
        final AtomicInteger inside = new AtomicInteger();
        final AtomicInteger peak = new AtomicInteger();
        final Set<Thread> threads = ConcurrentHashMap.newKeySet();
        final AtomicInteger virtualCalls = new AtomicInteger();

        FakeIssuer(Duration latency) { this.latency = latency; }

        String authorize(String paymentId) throws InterruptedException {
            Thread me = Thread.currentThread();
            threads.add(me);
            if (me.isVirtual()) virtualCalls.incrementAndGet();
            peak.accumulateAndGet(inside.incrementAndGet(), Math::max);
            try {
                Thread.sleep(latency);
                return "auth:" + paymentId;
            } finally {
                inside.decrementAndGet();
            }
        }
    }

    static List<String> ids(int n) {
        List<String> ids = new ArrayList<>(n);
        for (int i = 0; i < n; i++) ids.add("pay-" + i);
        return ids;
    }

    @Test
    @DisplayName("callAll returns the results in input order, even when later calls finish first")
    void keepsInputOrder() throws Exception {
        List<Integer> delays = List.of(80, 60, 40, 20, 0);
        List<String> out = FanOut.callAll(delays, ms -> {
            Thread.sleep(ms);
            return "slept " + ms;
        });
        assertThat(out).containsExactly("slept 80", "slept 60", "slept 40", "slept 20", "slept 0");
    }

    @Test
    @DisplayName("callAll runs 5,000 calls, each on its own new virtual thread")
    void oneVirtualThreadPerCall() throws Exception {
        FakeIssuer issuer = new FakeIssuer(Duration.ofMillis(10));
        List<String> out = FanOut.callAll(ids(5_000), issuer::authorize);
        assertThat(out).hasSize(5_000).startsWith("auth:pay-0").endsWith("auth:pay-4999");
        assertThat(issuer.virtualCalls.get()).as("calls that ran on a virtual thread").isEqualTo(5_000);
        assertThat(issuer.threads).as("distinct threads: one per call, never reused").hasSize(5_000);
        assertThat(issuer.peak.get()).as("calls in flight at once, with no limit").isGreaterThan(100);
    }

    @Test
    @DisplayName("callAll reports a failed call as an ExecutionException that carries the original cause")
    void failureSurfaces() {
        assertThatThrownBy(() -> FanOut.callAll(List.of("ok-1", "declined", "ok-2"), id -> {
            if (id.equals("declined")) throw new IllegalStateException("issuer declined " + id);
            return id;
        }))
                .isInstanceOf(ExecutionException.class)
                .hasCauseInstanceOf(IllegalStateException.class)
                .cause().hasMessage("issuer declined declined");
    }

    @Test
    @DisplayName("Bulkhead(20): 5,000 virtual threads, never more than 20 inside the issuer at once")
    void bulkheadCapsInFlight() throws Exception {
        FakeIssuer issuer = new FakeIssuer(Duration.ofMillis(4));
        Bulkhead limit = new Bulkhead(20);
        List<String> out = FanOut.callAll(ids(5_000), id -> limit.call(() -> issuer.authorize(id)));
        assertThat(out).hasSize(5_000);
        assertThat(issuer.peak.get()).as("most calls inside the issuer at once").isLessThanOrEqualTo(20);
        // proves the calls overlap; the margin is wide so a busy machine can't fail it
        assertThat(issuer.peak.get()).as("calls must still run in parallel up to the limit").isGreaterThanOrEqualTo(10);
        assertThat(limit.available()).as("free slots after everything finished").isEqualTo(20);
    }

    @Test
    @DisplayName("Bulkhead: two fan-outs at the same time share one limit of 20")
    void limitIsShared() throws Exception {
        FakeIssuer issuer = new FakeIssuer(Duration.ofMillis(4));
        Bulkhead limit = new Bulkhead(20);
        // two request handlers fan out at the same time through the same bulkhead
        List<List<String>> both = FanOut.callAll(List.of("a", "b"), batch ->
                FanOut.callAll(ids(1_000), id -> limit.call(() -> issuer.authorize(batch + id))));
        assertThat(both.get(0)).hasSize(1_000);
        assertThat(both.get(1)).hasSize(1_000);
        assertThat(issuer.peak.get()).as("most calls inside the issuer at once, across both").isLessThanOrEqualTo(20);
    }

    @Test
    @DisplayName("Bulkhead gives the slot back when the call throws")
    void releasesOnFailure() throws Exception {
        Bulkhead limit = new Bulkhead(3);
        for (int i = 0; i < 10; i++) {
            assertThatThrownBy(() -> limit.call(() -> { throw new IllegalStateException("timeout"); }))
                    .isInstanceOf(IllegalStateException.class);
        }
        assertThat(limit.available()).isEqualTo(3);
        assertThat(limit.call(() -> "still works")).isEqualTo("still works");
    }
}
