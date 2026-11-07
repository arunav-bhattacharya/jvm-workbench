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

class ResilientAuthorizerTest {

    /** An issuer that follows a script: the n-th call gets the n-th answer (the last one repeats). */
    static final class ScriptedIssuer implements CardIssuer {
        final AtomicInteger calls = new AtomicInteger();
        final AtomicInteger cancelled = new AtomicInteger();
        private final List<Supplier<Mono<String>>> script;

        ScriptedIssuer(List<Supplier<Mono<String>>> script) {
            this.script = script;
        }

        @Override
        public Mono<String> authorize(String paymentId) {
            int n = calls.incrementAndGet();
            // the answer is picked HERE, when authorize() is called, like a client that builds its request eagerly
            return script.get(Math.min(n, script.size()) - 1).get()
                    .doOnCancel(cancelled::incrementAndGet);
        }
    }

    static Supplier<Mono<String>> unavailable() {
        return () -> Mono.error(new IssuerUnavailableException("issuer busy"));
    }

    static Supplier<Mono<String>> approved() {
        return () -> Mono.just("APPROVED");
    }

    static Supplier<Mono<String>> declined() {
        return () -> Mono.error(new CardDeclinedException("insufficient funds"));
    }

    static Supplier<Mono<String>> hangs() {
        return Mono::never;
    }

    @Test
    @DisplayName("calling authorize() does not call the issuer until someone subscribes")
    void nothingHappensBeforeSubscribe() {
        ScriptedIssuer issuer = new ScriptedIssuer(List.of(approved()));

        Mono<String> pending = new ResilientAuthorizer(issuer).authorize("p-0");
        assertThat(issuer.calls).as("issuer calls before subscribe").hasValue(0);

        StepVerifier.create(pending).expectNext("APPROVED").expectComplete().verify(Duration.ofSeconds(5));
        assertThat(issuer.calls).as("issuer calls after subscribe").hasValue(1);
    }

    @Test
    @DisplayName("succeeds on the third attempt, after waiting 100 ms and then 200 ms")
    void retriesWithBackoff() {
        ScriptedIssuer issuer = new ScriptedIssuer(List.of(unavailable(), unavailable(), approved()));

        StepVerifier.withVirtualTime(() -> new ResilientAuthorizer(issuer).authorize("p-1"))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(299))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("APPROVED")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(issuer.calls).as("issuer calls").hasValue(3);
    }

    @Test
    @DisplayName("after 4 failed attempts (100 + 200 + 400 ms of backoff) it falls back to PENDING")
    void fallsBackWhenExhausted() {
        ScriptedIssuer issuer = new ScriptedIssuer(List.of(unavailable()));

        StepVerifier.withVirtualTime(() -> new ResilientAuthorizer(issuer).authorize("p-2"))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(699))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("PENDING:p-2")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(issuer.calls).as("issuer calls").hasValue(4);
    }

    @Test
    @DisplayName("a decline is passed straight to the caller, with no retry")
    void neverRetriesADecline() {
        ScriptedIssuer issuer = new ScriptedIssuer(List.of(declined(), approved()));

        StepVerifier.withVirtualTime(() -> new ResilientAuthorizer(issuer).authorize("p-3"))
                .expectSubscription()
                .expectErrorSatisfies(e -> assertThat(e)
                        .isInstanceOf(CardDeclinedException.class)
                        .hasMessage("insufficient funds"))
                .verify(Duration.ofSeconds(5));

        assertThat(issuer.calls).as("issuer calls").hasValue(1);
    }

    @Test
    @DisplayName("an attempt that hangs is cancelled after 500 ms and retried after 100 ms more")
    void timesOutAHangingAttempt() {
        ScriptedIssuer issuer = new ScriptedIssuer(List.of(hangs(), approved()));

        StepVerifier.withVirtualTime(() -> new ResilientAuthorizer(issuer).authorize("p-4"))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(599))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("APPROVED")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(issuer.calls).as("issuer calls").hasValue(2);
        assertThat(issuer.cancelled).as("hanging attempts cancelled").hasValue(1);
    }
}
