package workbench.executors.l06;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.Set;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CheckoutTest {
    private final AtomicInteger ids = new AtomicInteger();
    private final ExecutorService io = pool("io-", 4);

    private ExecutorService pool(String prefix, int n) {
        return Executors.newFixedThreadPool(n, r -> {
            Thread t = new Thread(r, prefix + ids.incrementAndGet());
            t.setDaemon(true);
            return t;
        });
    }

    @AfterEach
    void stop() {
        io.shutdownNow();
    }

    /** A gateway that records each charge and answers at once with ch_1, ch_2, ... */
    static final class RecordingGateway implements PaymentGateway {
        final List<BigDecimal> charged = new CopyOnWriteArrayList<>();
        final AtomicInteger next = new AtomicInteger();

        @Override
        public CompletableFuture<String> charge(String cartId, BigDecimal amount, String currency) {
            charged.add(amount);
            return CompletableFuture.completedFuture("ch_" + next.incrementAndGet());
        }
    }

    @Test
    @DisplayName("checkout converts the EUR price, charges it, and returns a receipt")
    void happyPath() throws Exception {
        RecordingGateway gateway = new RecordingGateway();
        Checkout checkout = new Checkout(cart -> new BigDecimal("100.00"), (from, to) -> new BigDecimal("1.0842"), gateway, io);

        Receipt receipt = checkout.checkout("cart-7", "USD").get(5, TimeUnit.SECONDS);

        assertThat(receipt).isEqualTo(new Receipt("cart-7", new BigDecimal("108.42"), "USD", "ch_1"));
        assertThat(gateway.charged).containsExactly(new BigDecimal("108.42"));
    }

    @Test
    @DisplayName("checkout rounds half-even to 2 decimals: 3.15 x 1.5 = 4.725 -> 4.72")
    void roundsHalfEven() throws Exception {
        Checkout checkout = new Checkout(cart -> new BigDecimal("3.15"), (from, to) -> new BigDecimal("1.5"), new RecordingGateway(), io);
        assertThat(checkout.checkout("cart-1", "CHF").get(5, TimeUnit.SECONDS).amount()).isEqualTo(new BigDecimal("4.72"));
    }

    @Test
    @DisplayName("checkout fetches price and FX rate at the same time")
    void fetchesInParallel() throws Exception {
        // each call waits at the barrier for the other; this only works if they overlap
        CyclicBarrier both = new CyclicBarrier(2);
        PriceService price = cart -> { meet(both); return new BigDecimal("10.00"); };
        FxService rate = (from, to) -> { meet(both); return new BigDecimal("2"); };
        Checkout checkout = new Checkout(price, rate, new RecordingGateway(), io);
        assertThat(checkout.checkout("cart-2", "PLN").get(10, TimeUnit.SECONDS).amount()).isEqualTo(new BigDecimal("20.00"));
    }

    private static void meet(CyclicBarrier barrier) {
        try {
            barrier.await(5, TimeUnit.SECONDS);
        } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
            throw new IllegalStateException("price and rate did not run at the same time", e);
        }
    }

    @Test
    @DisplayName("checkout runs the blocking calls on the io executor and returns without blocking")
    void usesIoAndDoesNotBlock() throws Exception {
        Set<String> threads = ConcurrentHashMap.newKeySet();
        CountDownLatch release = new CountDownLatch(1);
        PriceService price = cart -> {
            threads.add(Thread.currentThread().getName());
            try { release.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new BigDecimal("50.00");
        };
        FxService rate = (from, to) -> { threads.add(Thread.currentThread().getName()); return BigDecimal.ONE; };
        Checkout checkout = new Checkout(price, rate, new RecordingGateway(), io);

        CompletableFuture<Receipt> f = checkout.checkout("cart-3", "EUR");   // must return while the price call blocks
        assertThat(f.isDone()).as("done before the price arrived?").isFalse();
        release.countDown();
        assertThat(f.get(5, TimeUnit.SECONDS).amount()).isEqualTo(new BigDecimal("50.00"));
        assertThat(threads).isNotEmpty().allMatch(name -> name.startsWith("io-"), "runs on io-* threads");
    }

    @Test
    @DisplayName("checkout never charges when the FX call fails, and fails with that cause")
    void noChargeOnFailure() {
        RecordingGateway gateway = new RecordingGateway();
        IllegalStateException down = new IllegalStateException("FX provider down");
        Checkout checkout = new Checkout(cart -> BigDecimal.TEN, (from, to) -> { throw down; }, gateway, io);

        CompletableFuture<Receipt> f = checkout.checkout("cart-4", "USD");
        assertThatThrownBy(() -> f.get(5, TimeUnit.SECONDS)).hasCause(down);
        assertThatThrownBy(f::join).isInstanceOf(CompletionException.class).hasCause(down);
        assertThat(gateway.charged).as("charges made").isEmpty();
    }

    @Test
    @DisplayName("checkout doesn't block an io thread while the gateway's own future is pending")
    void composesTheCharge() throws Exception {
        ExecutorService single = pool("io1-", 1);
        try {
            CompletableFuture<String> pendingCharge = new CompletableFuture<>();
            CountDownLatch chargeCalled = new CountDownLatch(1);
            PaymentGateway slowGateway = (cart, amount, currency) -> { chargeCalled.countDown(); return pendingCharge; };
            Checkout checkout = new Checkout(cart -> BigDecimal.ONE, (from, to) -> BigDecimal.ONE, slowGateway, single);

            CompletableFuture<Receipt> f = checkout.checkout("cart-5", "EUR");
            assertThat(chargeCalled.await(5, TimeUnit.SECONDS)).as("gateway called").isTrue();

            // the only io thread must be free again: a probe task has to run while the charge is still pending
            CompletableFuture<String> probe = CompletableFuture.supplyAsync(() -> "free", single);
            assertThat(probe.get(5, TimeUnit.SECONDS)).as("io thread free while the charge is pending").isEqualTo("free");
            assertThat(f.isDone()).isFalse();

            pendingCharge.complete("ch_42");
            assertThat(f.get(5, TimeUnit.SECONDS).chargeId()).isEqualTo("ch_42");
        } finally {
            single.shutdownNow();
        }
    }
}
