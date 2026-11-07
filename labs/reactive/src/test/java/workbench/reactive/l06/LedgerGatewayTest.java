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

class LedgerGatewayTest {

    /**
     * A blocking ledger that records who called it. The balance of "acc-7" is 70.
     * The first {@code gate} callers wait (up to 500 ms) until that many calls are running at once,
     * so a solution that runs 4 calls together always reaches 4. Later accounts answer faster,
     * so results come back out of order unless the code puts them back in order.
     */
    static final class FakeLedger implements BlockingLedger {
        final AtomicInteger calls = new AtomicInteger();
        final AtomicInteger inFlight = new AtomicInteger();
        final AtomicInteger maxInFlight = new AtomicInteger();
        final Set<String> threads = ConcurrentHashMap.newKeySet();
        private final CountDownLatch gate;

        FakeLedger(int gate) {
            this.gate = new CountDownLatch(gate);
        }

        @Override
        public BigDecimal balance(String account) {
            calls.incrementAndGet();
            threads.add(Thread.currentThread().getName());
            int n = Integer.parseInt(account.substring(4));
            maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
            try {
                gate.countDown();
                gate.await(500, TimeUnit.MILLISECONDS);
                Thread.sleep(5L * (21 - n));                          // acc-1 is the slowest
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                inFlight.decrementAndGet();
            }
            return BigDecimal.valueOf(n * 10L);
        }
    }

    static final FxRates RATE = () -> Mono.delay(Duration.ofMillis(10)).thenReturn(new BigDecimal("0.92"));

    static List<String> accounts(int n) {
        return IntStream.rangeClosed(1, n).mapToObj(i -> "acc-" + i).toList();
    }

    @Test
    @DisplayName("balance() does not call the ledger until someone subscribes")
    void balanceIsLazy() {
        FakeLedger ledger = new FakeLedger(1);
        Mono<BigDecimal> balance = new LedgerGateway(ledger, RATE).balance("acc-7");
        assertThat(ledger.calls).as("ledger calls before subscribe").hasValue(0);

        StepVerifier.create(balance).expectNext(BigDecimal.valueOf(70)).expectComplete().verify(Duration.ofSeconds(5));
        assertThat(ledger.calls).as("ledger calls after subscribe").hasValue(1);
    }

    @Test
    @DisplayName("balance() runs the blocking call on a boundedElastic thread, not the caller's")
    void balanceRunsOnBoundedElastic() {
        FakeLedger ledger = new FakeLedger(1);
        StepVerifier.create(new LedgerGateway(ledger, RATE).balance("acc-3"))
                .expectNext(BigDecimal.valueOf(30)).expectComplete().verify(Duration.ofSeconds(5));
        assertThat(ledger.threads).as("threads that ran the ledger call")
                .hasSize(1)
                .allSatisfy(name -> assertThat(name).startsWith("boundedElastic-"));
    }

    @Test
    @DisplayName("balances() runs 4 ledger calls at the same time, and never more than 4")
    void balancesUsesFourAtATime() {
        FakeLedger ledger = new FakeLedger(4);
        StepVerifier.create(new LedgerGateway(ledger, RATE).balances(accounts(20)))
                .expectNextCount(20).expectComplete().verify(Duration.ofSeconds(10));
        assertThat(ledger.calls).as("ledger calls").hasValue(20);
        assertThat(ledger.maxInFlight).as("most ledger calls running at once").hasValue(4);
    }

    @Test
    @DisplayName("balances() returns the balances in the same order as the accounts")
    void balancesKeepOrder() {
        FakeLedger ledger = new FakeLedger(4);
        List<BigDecimal> expected = IntStream.rangeClosed(1, 12).mapToObj(i -> BigDecimal.valueOf(i * 10L)).toList();
        StepVerifier.create(new LedgerGateway(ledger, RATE).balances(accounts(12)))
                .expectNextSequence(expected).expectComplete().verify(Duration.ofSeconds(10));
    }

    @Test
    @DisplayName("toEur() works when the amount arrives on a parallel thread")
    void toEurDoesNotBlock() {
        Mono<BigDecimal> usdOnParallel = Mono.delay(Duration.ofMillis(10)).thenReturn(new BigDecimal("100"));
        StepVerifier.create(new LedgerGateway(new FakeLedger(1), RATE).toEur(usdOnParallel))
                .assertNext(eur -> assertThat(eur).isEqualByComparingTo("92"))
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }
}
