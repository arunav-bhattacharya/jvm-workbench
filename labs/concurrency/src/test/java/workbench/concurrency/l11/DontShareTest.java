package workbench.concurrency.l11;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DontShareTest {
    private final ExecutorService oneThread = Executors.newSingleThreadExecutor();   // a pool of one: every task reuses the thread

    @AfterEach
    void shutdown() {
        oneThread.shutdownNow();
    }

    private static List<FxQuote.Tier> tiers() {
        List<FxQuote.Tier> t = new ArrayList<>();
        t.add(new FxQuote.Tier(1_000_000, new BigDecimal("1.0842")));
        t.add(new FxQuote.Tier(10_000_000, new BigDecimal("1.0839")));
        return t;
    }

    // ---------- FxQuote ----------

    @Test
    @DisplayName("FxQuote: changing the list you passed in does not change the quote")
    void callerListCopied() {
        List<FxQuote.Tier> source = tiers();
        FxQuote q = new FxQuote("EURUSD", source, new byte[] {1, 2, 3});
        source.add(new FxQuote.Tier(99_000_000, new BigDecimal("9.9999")));
        source.set(0, new FxQuote.Tier(1, BigDecimal.ONE));
        assertThat(q.tiers()).hasSize(2);
        assertThat(q.tiers().get(0).rate()).isEqualByComparingTo("1.0842");
    }

    @Test
    @DisplayName("FxQuote: the list returned by tiers() cannot be modified")
    void tiersUnmodifiable() {
        FxQuote q = new FxQuote("EURUSD", tiers(), new byte[] {1, 2, 3});
        assertThatThrownBy(() -> q.tiers().add(new FxQuote.Tier(5, BigDecimal.TEN)))
                .isInstanceOf(UnsupportedOperationException.class);
        assertThat(q.tiers()).hasSize(2);
    }

    @Test
    @DisplayName("FxQuote: neither the array you passed in nor the one signature() returns can change the quote")
    void signatureCopiedBothWays() {
        byte[] sig = {7, 7, 7};
        FxQuote q = new FxQuote("EURUSD", tiers(), sig);
        sig[0] = 0;                                   // the caller changes its array
        q.signature()[1] = 0;                         // a reader changes the array it was given
        assertThat(q.signature()).containsExactly(7, 7, 7);
    }

    // ---------- TenantScope ----------

    @Test
    @DisplayName("TenantScope: on a reused pool thread, a request with no tenant does not see the previous request's tenant")
    void noBleedBetweenRequests() throws Exception {
        String first = oneThread.submit(() -> TenantScope.runAs("acme-retail", TenantScope::current)).get();
        String second = oneThread.submit(() -> TenantScope.runAs(null, TenantScope::current)).get();
        String afterwards = oneThread.submit(TenantScope::current).get();
        assertThat(first).isEqualTo("acme-retail");
        assertThat(second).as("tenant seen by the next request on the same thread").isEqualTo("none");
        assertThat(afterwards).as("tenant left on the thread after both requests").isEqualTo("none");
    }

    @Test
    @DisplayName("TenantScope: when the work throws, nothing is left behind on the thread")
    void clearedAfterException() throws Exception {
        Throwable thrown = oneThread.submit(() -> {
            try {
                TenantScope.runAs("globex", () -> { throw new IllegalStateException("issuer timeout"); });
                return null;
            } catch (IllegalStateException e) {
                return e;
            }
        }).get();
        assertThat(thrown).isInstanceOf(IllegalStateException.class);
        assertThat(oneThread.submit(TenantScope::current).get()).isEqualTo("none");
    }

    @Test
    @DisplayName("TenantScope: a nested runAs gives the outer tenant back when it ends")
    void nestedRestoresOuter() throws Exception {
        String seen = oneThread.submit(() -> TenantScope.runAs("acme-retail", () -> {
            String inner = TenantScope.runAs("initech", TenantScope::current);
            return inner + "," + TenantScope.current();
        })).get();
        assertThat(seen).isEqualTo("initech,acme-retail");
        assertThat(oneThread.submit(TenantScope::current).get()).isEqualTo("none");
    }
}
