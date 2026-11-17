package workbench.reactive.l06;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;

class ShopStockTest {

    /**
     * A blocking stock book that records who called it. "shop-7" has 70 loaves left.
     * The first {@code gate} callers wait (up to 500 ms) until that many calls are running at once,
     * so a solution that runs 4 calls together always reaches 4. Later shops answer faster,
     * so results come back out of order unless the code puts them back in order.
     */
    static final class FakeStockBook implements StockBook {
        final AtomicInteger calls = new AtomicInteger();
        final AtomicInteger inFlight = new AtomicInteger();
        final AtomicInteger maxInFlight = new AtomicInteger();
        final Set<String> threads = ConcurrentHashMap.newKeySet();
        private final CountDownLatch gate;

        FakeStockBook(int gate) {
            this.gate = new CountDownLatch(gate);
        }

        @Override
        public int loavesLeft(String shop) {
            calls.incrementAndGet();
            threads.add(Thread.currentThread().getName());
            int n = Integer.parseInt(shop.substring(5));
            maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
            try {
                gate.countDown();
                gate.await(500, TimeUnit.MILLISECONDS);
                Thread.sleep(5L * (21 - n));                          // shop-1 is the slowest
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                inFlight.decrementAndGet();
            }
            return n * 10;
        }
    }

    static final PriceList PRICE = () -> Mono.delay(Duration.ofMillis(10)).thenReturn(new BigDecimal("2.50"));

    static List<String> shops(int n) {
        return IntStream.rangeClosed(1, n).mapToObj(i -> "shop-" + i).toList();
    }

    @Test
    @DisplayName("loavesLeft() does not call the stock book until someone subscribes")
    void loavesLeftIsLazy() {
        FakeStockBook stock = new FakeStockBook(1);
        Mono<Integer> left = new ShopStock(stock, PRICE).loavesLeft("shop-7");
        assertThat(stock.calls).as("stock-book calls before subscribe").hasValue(0);

        StepVerifier.create(left).expectNext(70).expectComplete().verify(Duration.ofSeconds(5));
        assertThat(stock.calls).as("stock-book calls after subscribe").hasValue(1);
    }

    @Test
    @DisplayName("loavesLeft() runs the blocking call on a boundedElastic thread, not the caller's")
    void loavesLeftRunsOnBoundedElastic() {
        FakeStockBook stock = new FakeStockBook(1);
        StepVerifier.create(new ShopStock(stock, PRICE).loavesLeft("shop-3"))
                .expectNext(30).expectComplete().verify(Duration.ofSeconds(5));
        assertThat(stock.threads).as("threads that ran the stock-book call")
                .hasSize(1)
                .allSatisfy(name -> assertThat(name).startsWith("boundedElastic-"));
    }

    @Test
    @DisplayName("loavesLeftIn() runs 4 stock-book calls at the same time, and never more than 4")
    void loavesLeftInUsesFourAtATime() {
        FakeStockBook stock = new FakeStockBook(4);
        StepVerifier.create(new ShopStock(stock, PRICE).loavesLeftIn(shops(20)))
                .expectNextCount(20).expectComplete().verify(Duration.ofSeconds(10));
        assertThat(stock.calls).as("stock-book calls").hasValue(20);
        assertThat(stock.maxInFlight).as("most stock-book calls running at once").hasValue(4);
    }

    @Test
    @DisplayName("loavesLeftIn() returns the counts in the same order as the shops")
    void loavesLeftInKeepsOrder() {
        FakeStockBook stock = new FakeStockBook(4);
        List<Integer> expected = IntStream.rangeClosed(1, 12).mapToObj(i -> i * 10).toList();
        StepVerifier.create(new ShopStock(stock, PRICE).loavesLeftIn(shops(12)))
                .expectNextSequence(expected).expectComplete().verify(Duration.ofSeconds(10));
    }

    @Test
    @DisplayName("stockValue() works when the count arrives on a parallel thread")
    void stockValueDoesNotBlock() {
        Mono<Integer> loavesOnParallel = Mono.delay(Duration.ofMillis(10)).thenReturn(100);
        StepVerifier.create(new ShopStock(new FakeStockBook(1), PRICE).stockValue(loavesOnParallel))
                .assertNext(value -> assertThat(value).isEqualByComparingTo("250"))
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }
}
