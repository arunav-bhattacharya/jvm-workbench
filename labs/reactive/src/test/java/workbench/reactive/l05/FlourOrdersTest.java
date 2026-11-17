package workbench.reactive.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;

class FlourOrdersTest {

    /** A mill that follows a script: the n-th call gets the n-th answer (the last one repeats). */
    static final class ScriptedMill implements Mill {
        final AtomicInteger calls = new AtomicInteger();
        final AtomicInteger cancelled = new AtomicInteger();
        private final List<Supplier<Mono<String>>> script;

        ScriptedMill(List<Supplier<Mono<String>>> script) {
            this.script = script;
        }

        @Override
        public Mono<String> order(String orderId) {
            int n = calls.incrementAndGet();
            // the answer is picked HERE, when order() is called, like a client that builds its request eagerly
            return script.get(Math.min(n, script.size()) - 1).get()
                    .doOnCancel(cancelled::incrementAndGet);
        }
    }

    static Supplier<Mono<String>> busy() {
        return () -> Mono.error(new MillBusyException("mill busy"));
    }

    static Supplier<Mono<String>> confirmed() {
        return () -> Mono.just("CONFIRMED");
    }

    static Supplier<Mono<String>> refused() {
        return () -> Mono.error(new OrderRefusedException("no rye flour this week"));
    }

    static Supplier<Mono<String>> hangs() {
        return Mono::never;
    }

    @Test
    @DisplayName("calling place() does not call the mill until someone subscribes")
    void nothingHappensBeforeSubscribe() {
        ScriptedMill mill = new ScriptedMill(List.of(confirmed()));

        Mono<String> pending = new FlourOrders(mill).place("flour-0");
        assertThat(mill.calls).as("mill calls before subscribe").hasValue(0);

        StepVerifier.create(pending).expectNext("CONFIRMED").expectComplete().verify(Duration.ofSeconds(5));
        assertThat(mill.calls).as("mill calls after subscribe").hasValue(1);
    }

    @Test
    @DisplayName("succeeds on the third attempt, after waiting 100 ms and then 200 ms")
    void retriesWithBackoff() {
        ScriptedMill mill = new ScriptedMill(List.of(busy(), busy(), confirmed()));

        StepVerifier.withVirtualTime(() -> new FlourOrders(mill).place("flour-1"))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(299))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("CONFIRMED")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(mill.calls).as("mill calls").hasValue(3);
    }

    @Test
    @DisplayName("after 4 failed attempts (100 + 200 + 400 ms of backoff) it falls back to PENDING")
    void fallsBackWhenExhausted() {
        ScriptedMill mill = new ScriptedMill(List.of(busy()));

        StepVerifier.withVirtualTime(() -> new FlourOrders(mill).place("flour-2"))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(699))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("PENDING:flour-2")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(mill.calls).as("mill calls").hasValue(4);
    }

    @Test
    @DisplayName("a refusal is passed straight to the caller, with no retry")
    void neverRetriesARefusal() {
        ScriptedMill mill = new ScriptedMill(List.of(refused(), confirmed()));

        StepVerifier.withVirtualTime(() -> new FlourOrders(mill).place("flour-3"))
                .expectSubscription()
                .expectErrorSatisfies(e -> assertThat(e)
                        .isInstanceOf(OrderRefusedException.class)
                        .hasMessage("no rye flour this week"))
                .verify(Duration.ofSeconds(5));

        assertThat(mill.calls).as("mill calls").hasValue(1);
    }

    @Test
    @DisplayName("an attempt that hangs is cancelled after 500 ms and retried after 100 ms more")
    void timesOutAHangingAttempt() {
        ScriptedMill mill = new ScriptedMill(List.of(hangs(), confirmed()));

        StepVerifier.withVirtualTime(() -> new FlourOrders(mill).place("flour-4"))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(599))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("CONFIRMED")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(mill.calls).as("mill calls").hasValue(2);
        assertThat(mill.cancelled).as("hanging attempts cancelled").hasValue(1);
    }
}
