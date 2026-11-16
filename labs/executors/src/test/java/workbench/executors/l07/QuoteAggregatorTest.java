package workbench.executors.l07;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.math.BigDecimal;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class QuoteAggregatorTest {
    private static final Duration TIMEOUT = Duration.ofMillis(200);

    private final AtomicInteger ids = new AtomicInteger();
    private final ExecutorService io = Executors.newFixedThreadPool(8, r -> {
        Thread t = new Thread(r, "io-" + ids.incrementAndGet());
        t.setDaemon(true);
        return t;
    });
    // a slow supplier waits on this; it is released after each test
    private final CountDownLatch never = new CountDownLatch(1);
    private final Map<String, Throwable> skipped = new ConcurrentHashMap<>();

    @AfterEach
    void stop() {
        never.countDown();
        io.shutdownNow();
    }

    private static QuoteProvider provider(String name, Function<String, BigDecimal> quote) {
        return new QuoteProvider() {
            @Override public String name() { return name; }
            @Override public BigDecimal quote(String item) { return quote.apply(item); }
        };
    }

    private static QuoteProvider fixed(String name, String price) {
        return provider(name, item -> new BigDecimal(price));
    }

    private QuoteProvider hanging(String name) {
        return provider(name, item -> {
            try {
                never.await();                      // far slower than the timeout
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return new BigDecimal("0.01");        // would win, if anyone still listened
        });
    }

    private QuoteAggregator aggregator(QuoteProvider... providers) {
        return new QuoteAggregator(List.of(providers), io, TIMEOUT, skipped::put);
    }

    @Test
    @DisplayName("best picks the lowest quote among the suppliers")
    void picksLowest() throws Exception {
        QuoteAggregator agg = aggregator(fixed("alpha", "21.50"), fixed("beta", "19.80"), fixed("gamma", "22.10"));
        assertThat(agg.best("flour").get(5, TimeUnit.SECONDS)).isEqualTo(new Quote("beta", new BigDecimal("19.80")));
        assertThat(skipped).isEmpty();
    }

    @Test
    @DisplayName("best asks every supplier at the same time")
    void asksInParallel() throws Exception {
        // each supplier waits at the barrier for the other two; this only works if all three overlap
        CyclicBarrier all = new CyclicBarrier(3);
        Function<String, BigDecimal> meet = item -> {
            try {
                all.await(5, TimeUnit.SECONDS);
            } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                throw new IllegalStateException("the suppliers were not asked at the same time", e);
            }
            return new BigDecimal("20.00");
        };
        QuoteAggregator agg = new QuoteAggregator(
                List.of(provider("a", meet), provider("b", meet), provider("c", meet)), io, Duration.ofSeconds(10), skipped::put);
        assertThat(agg.best("flour").get(10, TimeUnit.SECONDS).price()).isEqualTo(new BigDecimal("20.00"));
        assertThat(skipped).as("skipped suppliers").isEmpty();
    }

    @Test
    @DisplayName("a supplier that throws is skipped and reported with its own exception, not a CompletionException")
    void skipsFailingProvider() throws Exception {
        IllegalStateException down = new IllegalStateException("flaky is closed today");
        QuoteAggregator agg = aggregator(provider("flaky", item -> { throw down; }), fixed("steady", "20.40"));

        assertThat(agg.best("flour").get(5, TimeUnit.SECONDS)).isEqualTo(new Quote("steady", new BigDecimal("20.40")));
        assertThat(skipped).containsOnlyKeys("flaky");
        assertThat(skipped.get("flaky")).isSameAs(down);
    }

    @Test
    @DisplayName("a supplier slower than its timeout is skipped and reported with a TimeoutException")
    void skipsSlowProvider() throws Exception {
        QuoteAggregator agg = aggregator(hanging("slow"), fixed("steady", "20.40"));

        // without a per-supplier timeout this never completes
        assertThat(agg.best("flour").get(5, TimeUnit.SECONDS)).isEqualTo(new Quote("steady", new BigDecimal("20.40")));
        assertThat(skipped).containsOnlyKeys("slow");
        assertThat(skipped.get("slow")).isInstanceOf(TimeoutException.class);
    }

    @Test
    @DisplayName("when every supplier is skipped, best fails with NoQuoteException")
    void failsWhenNobodyAnswers() {
        QuoteAggregator agg = aggregator(provider("flaky", item -> { throw new IllegalStateException("closed today"); }), hanging("slow"));

        CompletableFuture<Quote> f = agg.best("flour");
        assertThatThrownBy(() -> f.get(5, TimeUnit.SECONDS))
                .isInstanceOf(ExecutionException.class)
                .hasCauseInstanceOf(NoQuoteException.class);
        assertThatThrownBy(f::join).isInstanceOf(CompletionException.class).hasCauseInstanceOf(NoQuoteException.class);
        assertThat(skipped).containsOnlyKeys("flaky", "slow");
    }

    @Test
    @DisplayName("best returns at once, without waiting for the suppliers")
    void doesNotBlockTheCaller() throws Exception {
        CountDownLatch release = new CountDownLatch(1);
        QuoteProvider gated = provider("gated", item -> {
            try {
                release.await();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return new BigDecimal("20.90");
        });
        QuoteAggregator agg = new QuoteAggregator(List.of(gated), io, Duration.ofSeconds(10), skipped::put);

        CompletableFuture<Quote> f = agg.best("flour");     // must return while the supplier is still blocked
        assertThat(f.isDone()).as("done before the supplier answered?").isFalse();
        release.countDown();
        assertThat(f.get(5, TimeUnit.SECONDS).provider()).isEqualTo("gated");
    }

    @Test
    @DisplayName("unwrap strips CompletionException and ExecutionException layers, and nothing else")
    void unwrapStripsOnlyWrappers() {
        IOException io = new IOException("connection reset");
        assertThat(QuoteAggregator.unwrap(new CompletionException(new ExecutionException(io)))).isSameAs(io);
        assertThat(QuoteAggregator.unwrap(new CompletionException(io))).isSameAs(io);
        assertThat(QuoteAggregator.unwrap(io)).isSameAs(io);

        IllegalStateException other = new IllegalStateException("not a wrapper", io);
        assertThat(QuoteAggregator.unwrap(new CompletionException(other))).isSameAs(other);

        CompletionException empty = new CompletionException("no cause", null);
        assertThat(QuoteAggregator.unwrap(empty)).isSameAs(empty);
    }
}
