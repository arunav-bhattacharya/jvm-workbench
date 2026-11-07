package workbench.patterns.l09;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l09.FraudChain.Approve;
import workbench.patterns.l09.FraudChain.Chain;
import workbench.patterns.l09.FraudChain.Check;
import workbench.patterns.l09.FraudChain.Reject;
import workbench.patterns.l09.FraudChain.Request;
import workbench.patterns.l09.FraudChain.Review;
import workbench.patterns.l09.PaymentLifecycle.Authorize;
import workbench.patterns.l09.PaymentLifecycle.Authorized;
import workbench.patterns.l09.PaymentLifecycle.Capture;
import workbench.patterns.l09.PaymentLifecycle.Captured;
import workbench.patterns.l09.PaymentLifecycle.Created;
import workbench.patterns.l09.PaymentLifecycle.Decline;
import workbench.patterns.l09.PaymentLifecycle.Failed;
import workbench.patterns.l09.PaymentLifecycle.PaymentEvent;
import workbench.patterns.l09.PaymentLifecycle.PaymentState;
import workbench.patterns.l09.PaymentLifecycle.Refund;
import workbench.patterns.l09.PaymentLifecycle.Refunded;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static workbench.patterns.l09.PaymentLifecycle.replay;
import static workbench.patterns.l09.PaymentLifecycle.transition;

class StateChainTest {

    // ---- state ----

    @Test
    @DisplayName("Authorize, capture, then a partial refund ends in Refunded(p1, 2000)")
    void happyPath() {
        assertThat(replay("p1", List.of(new Authorize("A-77", 5_000), new Capture(), new Refund(2_000))))
                .isEqualTo(new Refunded("p1", 2_000));
    }

    @Test
    @DisplayName("Each allowed move produces the next state with the right data")
    void eachStep() {
        PaymentState authorized = transition(new Created("p1"), new Authorize("A-77", 5_000));
        assertThat(authorized).isEqualTo(new Authorized("p1", "A-77", 5_000));
        assertThat(transition(authorized, new Capture())).isEqualTo(new Captured("p1", 5_000));
        assertThat(transition(new Created("p2"), new Decline("issuer 51"))).isEqualTo(new Failed("p2", "issuer 51"));
        assertThat(transition(authorized, new Decline("risk"))).isEqualTo(new Failed("p1", "risk"));
    }

    @Test
    @DisplayName("Capture before authorize is rejected with a message naming the event and the state")
    void captureBeforeAuthorize() {
        assertThatThrownBy(() -> transition(new Created("p1"), new Capture()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Capture not allowed in Created");
    }

    @Test
    @DisplayName("Guards: no zero authorization, no zero refund, no refund above the captured amount")
    void guards() {
        assertThatThrownBy(() -> transition(new Created("p1"), new Authorize("A-77", 0)))
                .isInstanceOf(IllegalStateException.class).hasMessage("Authorize not allowed in Created");
        assertThatThrownBy(() -> transition(new Captured("p1", 5_000), new Refund(0)))
                .isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> transition(new Captured("p1", 5_000), new Refund(5_001)))
                .isInstanceOf(IllegalStateException.class).hasMessage("Refund not allowed in Captured");
        assertThat(transition(new Captured("p1", 5_000), new Refund(5_000))).isEqualTo(new Refunded("p1", 5_000));
    }

    @Test
    @DisplayName("Refunded and Failed are terminal: every event is rejected")
    void terminal() {
        List<PaymentEvent> all = List.of(new Authorize("A", 1), new Capture(), new Refund(1), new Decline("x"));
        for (PaymentState end : List.of(new Refunded("p1", 100), new Failed("p1", "x"))) {
            for (PaymentEvent e : all) {
                assertThatThrownBy(() -> transition(end, e)).as("%s in %s", e, end).isInstanceOf(IllegalStateException.class);
            }
        }
    }

    // ---- chain of responsibility ----

    private static final Request OK = new Request("p1", 5_000, "DE", "DE");
    private static final Request ABROAD_AND_BIG = new Request("p2", 900_000, "DE", "NG");

    private static Check counting(AtomicInteger calls) {
        return (r, next) -> { calls.incrementAndGet(); return next.proceed(r); };
    }

    @Test
    @DisplayName("A request that passes every check reaches the terminal step")
    void passesThrough() {
        AtomicInteger terminalCalls = new AtomicInteger();
        Chain chain = FraudChain.build(List.of(FraudChain.amountLimit(100_000), FraudChain.countryMismatch()),
                r -> { terminalCalls.incrementAndGet(); return new Approve(); });
        assertThat(chain.proceed(OK)).isEqualTo(new Approve());
        assertThat(terminalCalls.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("A check that decides stops the chain: later checks and the terminal never run")
    void shortCircuit() {
        AtomicInteger later = new AtomicInteger();
        AtomicInteger terminalCalls = new AtomicInteger();
        Chain chain = FraudChain.build(List.of(FraudChain.amountLimit(100_000), counting(later)),
                r -> { terminalCalls.incrementAndGet(); return new Approve(); });
        assertThat(chain.proceed(new Request("p3", 100_001, "DE", "DE"))).isEqualTo(new Reject("over limit"));
        assertThat(later.get()).isZero();
        assertThat(terminalCalls.get()).isZero();
    }

    @Test
    @DisplayName("Order is behavior: the first check that decides wins")
    void orderMatters() {
        Chain limitFirst = FraudChain.build(List.of(FraudChain.amountLimit(100_000), FraudChain.countryMismatch()), r -> new Approve());
        Chain countryFirst = FraudChain.build(List.of(FraudChain.countryMismatch(), FraudChain.amountLimit(100_000)), r -> new Approve());
        assertThat(limitFirst.proceed(ABROAD_AND_BIG)).isEqualTo(new Reject("over limit"));
        assertThat(countryFirst.proceed(ABROAD_AND_BIG)).isEqualTo(new Review("country mismatch"));
    }

    @Test
    @DisplayName("Checks run in list order, once each per request, and the chain can be reused")
    void onceEachAndReusable() {
        List<String> order = new ArrayList<>();
        Check a = (r, next) -> { order.add("a"); return next.proceed(r); };
        Check b = (r, next) -> { order.add("b"); return next.proceed(r); };
        List<Check> checks = new ArrayList<>(List.of(a, b));
        Chain chain = FraudChain.build(checks, r -> { order.add("end"); return new Approve(); });
        checks.add((r, next) -> new Reject("added after build"));      // must not change the built chain
        chain.proceed(OK);
        chain.proceed(OK);
        assertThat(order).containsExactly("a", "b", "end", "a", "b", "end");
    }

    @Test
    @DisplayName("An empty chain goes straight to the terminal step")
    void emptyChain() {
        assertThat(FraudChain.build(List.of(), r -> new Review("manual")).proceed(OK)).isEqualTo(new Review("manual"));
    }
}
