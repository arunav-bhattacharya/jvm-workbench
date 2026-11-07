package workbench.memory.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import javax.management.ObjectName;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class IdempotencyCacheTest {

    /** Live instances of a class, from the same class histogram `jcmd <pid> GC.class_histogram` prints. It runs a full GC first. */
    static long liveInstances(String className) throws Exception {
        String histogram = (String) ManagementFactory.getPlatformMBeanServer().invoke(
                new ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
                new Object[] {null}, new String[] {String[].class.getName()});
        for (String line : histogram.split("\n")) {
            String[] f = line.trim().split("\\s+");                 //    4:   20000   640000  workbench.memory.l07.PaymentResponse
            if (f.length >= 4 && f[3].equals(className)) return Long.parseLong(f[1]);
        }
        return 0;
    }

    static PaymentRequest request(int n) {
        String body = "{\"merchant\":\"m-" + (n % 50) + "\",\"amount\":" + (1_000 + n) + ",\"note\":\"" + "x".repeat(2_000) + "\"}";
        return new PaymentRequest("key-" + n, "m-" + (n % 50), 1_000 + n, body.getBytes(StandardCharsets.UTF_8));
    }

    static PaymentResponse approve(PaymentRequest r) {
        return new PaymentResponse("pay-" + r.idempotencyKey(), "APPROVED", r.amountMinor());
    }

    @Test
    @DisplayName("a retry gets the stored response, and the handler runs once")
    void retryGetsSameResponse() {
        IdempotencyCache cache = new IdempotencyCache(100);
        AtomicInteger charges = new AtomicInteger();
        PaymentResponse first = cache.getOrCompute(request(1), r -> { charges.incrementAndGet(); return approve(r); });
        PaymentResponse retry = cache.getOrCompute(request(1), r -> { charges.incrementAndGet(); return approve(r); });
        assertThat(retry).isEqualTo(first);
        assertThat(charges.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("a retry that reuses the key with a different body is rejected")
    void conflictingRetryIsRejected() {
        IdempotencyCache cache = new IdempotencyCache(100);
        cache.getOrCompute(request(1), IdempotencyCacheTest::approve);
        PaymentRequest tampered = new PaymentRequest("key-1", "m-1", 99_999, "{\"amount\":99999}".getBytes(StandardCharsets.UTF_8));
        assertThatThrownBy(() -> cache.getOrCompute(tampered, IdempotencyCacheTest::approve))
                .isInstanceOf(IdempotencyConflictException.class);
    }

    @Test
    @DisplayName("the cache never holds more than maxEntries responses")
    void bounded() {
        IdempotencyCache cache = new IdempotencyCache(500);
        for (int i = 0; i < 5_000; i++) cache.getOrCompute(request(i), IdempotencyCacheTest::approve);
        assertThat(cache.size()).isEqualTo(500);
    }

    @Test
    @DisplayName("the least recently used entry is dropped first")
    void leastRecentlyUsedGoesFirst() {
        IdempotencyCache cache = new IdempotencyCache(2);
        AtomicInteger charges = new AtomicInteger();
        cache.getOrCompute(request(1), r -> { charges.incrementAndGet(); return approve(r); });
        cache.getOrCompute(request(2), r -> { charges.incrementAndGet(); return approve(r); });
        cache.getOrCompute(request(1), r -> { charges.incrementAndGet(); return approve(r); });   // 1 is now the most recent
        cache.getOrCompute(request(3), r -> { charges.incrementAndGet(); return approve(r); });   // drops 2
        assertThat(charges.get()).isEqualTo(3);
        cache.getOrCompute(request(1), r -> { charges.incrementAndGet(); return approve(r); });
        assertThat(charges.get()).as("1 was still cached").isEqualTo(3);
        cache.getOrCompute(request(2), r -> { charges.incrementAndGet(); return approve(r); });
        assertThat(charges.get()).as("2 had been dropped, so the handler ran again").isEqualTo(4);
    }

    @Test
    @DisplayName("after 20,000 payments, no more than maxEntries responses are still alive on the heap")
    void responsesDoNotPileUp() throws Exception {
        IdempotencyCache cache = new IdempotencyCache(500);
        for (int i = 0; i < 20_000; i++) cache.getOrCompute(request(i), IdempotencyCacheTest::approve);
        assertThat(liveInstances("workbench.memory.l07.PaymentResponse")).isLessThanOrEqualTo(502);
        assertThat(cache.size()).isPositive();                   // keeps the cache reachable until the count is done
    }

    @Test
    @DisplayName("the cache keeps no request, and so no request body, alive")
    void requestBodiesAreNotRetained() throws Exception {
        IdempotencyCache cache = new IdempotencyCache(500);
        for (int i = 0; i < 20_000; i++) cache.getOrCompute(request(i), IdempotencyCacheTest::approve);
        assertThat(liveInstances("workbench.memory.l07.PaymentRequest")).isLessThanOrEqualTo(2);
        assertThat(cache.size()).isPositive();
    }
}
