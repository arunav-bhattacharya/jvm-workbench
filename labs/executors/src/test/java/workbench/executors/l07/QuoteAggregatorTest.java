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
    // a slow provider waits on this; it is released after each test
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
            @Override public BigDecimal quote(String pair) { return quote.apply(pair); }
        };
    }

    private static QuoteProvider fixed(String name, String price) {
        return provider(name, pair -> new BigDecimal(price));
    }

    private QuoteProvider hanging(String name) {
        return provider(name, pair -> {
            try {
                never.await();                      // far slower than the timeout
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return new BigDecimal("0.0001");        // would win, if anyone still listened
        });
    }

    private QuoteAggregator aggregator(QuoteProvider... providers) {
        return new QuoteAggregator(List.of(providers), io, TIMEOUT, skipped::put);
    }

    @Test
    @DisplayName("best picks the lowest quote among the providers")
    void picksLowest() throws Exception {
        QuoteAggregator agg = aggregator(fixed("alpha", "1.0850"), fixed("beta", "1.0842"), fixed("gamma", "1.0861"));
        assertThat(agg.best("EUR/USD").get(5, TimeUnit.SECONDS)).isEqualTo(new Quote("beta", new BigDecimal("1.0842")));
        assertThat(skipped).isEmpty();
    }

    @Test
    @DisplayName("best asks every provider at the same time")
    void asksInParallel() throws Exception {
        // each provider waits at the barrier for the other two; this only works if all three overlap
        CyclicBarrier all = new CyclicBarrier(3);
        Function<String, BigDecimal> meet = pair -> {
            try {
                all.await(5, TimeUnit.SECONDS);
            } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                throw new IllegalStateException("the providers were not asked at the same time", e);
            }
            return new BigDecimal("1.08");
        };
        QuoteAggregator agg = new QuoteAggregator(
                List.of(provider("a", meet), provider("b", meet), provider("c", meet)), io, Duration.ofSeconds(10), skipped::put);
        assertThat(agg.best("EUR/USD").get(10, TimeUnit.SECONDS).price()).isEqualTo(new BigDecimal("1.08"));
        assertThat(skipped).as("skipped providers").isEmpty();
    }

    @Test
    @DisplayName("a provider that throws is skipped and reported with its own exception, not a CompletionException")
    void skipsFailingProvider() throws Exception {
        IllegalStateException down = new IllegalStateException("502 from flaky");
        QuoteAggregator agg = aggregator(provider("flaky", pair -> { throw down; }), fixed("steady", "1.0900"));

        assertThat(agg.best("EUR/USD").get(5, TimeUnit.SECONDS)).isEqualTo(new Quote("steady", new BigDecimal("1.0900")));
        assertThat(skipped).containsOnlyKeys("flaky");
        assertThat(skipped.get("flaky")).isSameAs(down);
    }

    @Test
    @DisplayName("a provider slower than its timeout is skipped and reported with a TimeoutException")
    void skipsSlowProvider() throws Exception {
        QuoteAggregator agg = aggregator(hanging("slow"), fixed("steady", "1.0900"));

        // without a per-provider timeout this never completes
        assertThat(agg.best("EUR/USD").get(5, TimeUnit.SECONDS)).isEqualTo(new Quote("steady", new BigDecimal("1.0900")));
        assertThat(skipped).containsOnlyKeys("slow");
        assertThat(skipped.get("slow")).isInstanceOf(TimeoutException.class);
    }

    @Test
    @DisplayName("when every provider is skipped, best fails with NoQuoteException")
    void failsWhenNobodyAnswers() {
        QuoteAggregator agg = aggregator(provider("flaky", pair -> { throw new IllegalStateException("down"); }), hanging("slow"));

        CompletableFuture<Quote> f = agg.best("EUR/USD");
        assertThatThrownBy(() -> f.get(5, TimeUnit.SECONDS))
                .isInstanceOf(ExecutionException.class)
                .hasCauseInstanceOf(NoQuoteException.class);
        assertThatThrownBy(f::join).isInstanceOf(CompletionException.class).hasCauseInstanceOf(NoQuoteException.class);
        assertThat(skipped).containsOnlyKeys("flaky", "slow");
    }

    @Test
    @DisplayName("best returns at once, without waiting for the providers")
    void doesNotBlockTheCaller() throws Exception {
        CountDownLatch release = new CountDownLatch(1);
        QuoteProvider gated = provider("gated", pair -> {
            try {
                release.await();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return new BigDecimal("1.07");
        });
        QuoteAggregator agg = new QuoteAggregator(List.of(gated), io, Duration.ofSeconds(10), skipped::put);

        CompletableFuture<Quote> f = agg.best("EUR/USD");     // must return while the provider is still blocked
        assertThat(f.isDone()).as("done before the provider answered?").isFalse();
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
