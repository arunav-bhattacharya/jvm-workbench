package workbench.patterns.l09;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l09.ComplaintDesk.Chain;
import workbench.patterns.l09.ComplaintDesk.Complaint;
import workbench.patterns.l09.ComplaintDesk.Handler;
import workbench.patterns.l09.ComplaintDesk.Reply;
import workbench.patterns.l09.OrderLife.Cancel;
import workbench.patterns.l09.OrderLife.Cancelled;
import workbench.patterns.l09.OrderLife.Deliver;
import workbench.patterns.l09.OrderLife.Delivered;
import workbench.patterns.l09.OrderLife.OrderEvent;
import workbench.patterns.l09.OrderLife.OrderState;
import workbench.patterns.l09.OrderLife.OutForDelivery;
import workbench.patterns.l09.OrderLife.Pack;
import workbench.patterns.l09.OrderLife.Packed;
import workbench.patterns.l09.OrderLife.Placed;
import workbench.patterns.l09.OrderLife.Ship;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static workbench.patterns.l09.OrderLife.replay;
import static workbench.patterns.l09.OrderLife.transition;

class StateChainTest {

    // ---- state ----

    @Test
    @DisplayName("Pack, ship, then deliver ends in Delivered(7781, Ana)")
    void happyPath() {
        assertThat(replay("7781", List.of(new Pack(2), new Ship("Pedal Post"), new Deliver("Ana"))))
                .isEqualTo(new Delivered("7781", "Ana"));
    }

    @Test
    @DisplayName("Each allowed move produces the next state with the right data")
    void eachStep() {
        OrderState packed = transition(new Placed("7781"), new Pack(2));
        assertThat(packed).isEqualTo(new Packed("7781", 2));
        assertThat(transition(packed, new Ship("Pedal Post"))).isEqualTo(new OutForDelivery("7781", 2, "Pedal Post"));
        assertThat(transition(new Placed("7782"), new Cancel("changed my mind"))).isEqualTo(new Cancelled("7782", "changed my mind"));
        assertThat(transition(packed, new Cancel("out of jam"))).isEqualTo(new Cancelled("7781", "out of jam"));
    }

    @Test
    @DisplayName("Moves out of turn are rejected with a message naming the event and the state")
    void outOfTurn() {
        assertThatThrownBy(() -> transition(new Placed("7781"), new Ship("Pedal Post")))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Ship not allowed in Placed");
        assertThatThrownBy(() -> transition(new OutForDelivery("7781", 2, "Big Blue Vans"), new Cancel("too late")))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Cancel not allowed in OutForDelivery");
    }

    @Test
    @DisplayName("Guards: no packing zero parcels, no delivery without a signature")
    void guards() {
        assertThatThrownBy(() -> transition(new Placed("7781"), new Pack(0)))
                .isInstanceOf(IllegalStateException.class).hasMessage("Pack not allowed in Placed");
        OrderState out = new OutForDelivery("7781", 2, "Pedal Post");
        assertThatThrownBy(() -> transition(out, new Deliver("")))
                .isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> transition(out, new Deliver("   ")))
                .isInstanceOf(IllegalStateException.class).hasMessage("Deliver not allowed in OutForDelivery");
        assertThat(transition(out, new Deliver("Ana"))).isEqualTo(new Delivered("7781", "Ana"));
    }

    @Test
    @DisplayName("Delivered and Cancelled are final: every event is rejected")
    void finalStates() {
        List<OrderEvent> all = List.of(new Pack(1), new Ship("Pedal Post"), new Deliver("Ana"), new Cancel("x"));
        for (OrderState end : List.of(new Delivered("7781", "Ana"), new Cancelled("7781", "x"))) {
            for (OrderEvent e : all) {
                assertThatThrownBy(() -> transition(end, e)).as("%s in %s", e, end).isInstanceOf(IllegalStateException.class);
            }
        }
    }

    // ---- chain of responsibility ----

    private static final Reply HEAD_OFFICE = new Reply("head office", "we'll write to you");
    private static final Complaint SMALL = new Complaint("7781", "stale bread", 250);
    private static final Complaint LATE_AND_SMALL = new Complaint("7782", "late", 300);

    private static Handler counting(AtomicInteger calls) {
        return (c, next) -> { calls.incrementAndGet(); return next.passOn(c); };
    }

    @Test
    @DisplayName("A complaint nobody can sort reaches the last stop")
    void passesThrough() {
        AtomicInteger lastStopCalls = new AtomicInteger();
        Chain desk = ComplaintDesk.build(List.of(ComplaintDesk.upTo("assistant", 500), ComplaintDesk.upTo("manager", 5_000)),
                c -> { lastStopCalls.incrementAndGet(); return HEAD_OFFICE; });
        assertThat(desk.passOn(new Complaint("7790", "broken bike rack", 9_000))).isEqualTo(HEAD_OFFICE);
        assertThat(lastStopCalls.get()).isEqualTo(1);
        assertThat(desk.passOn(new Complaint("7791", "cracked teapot", 1_800))).isEqualTo(new Reply("manager", "sorted"));
    }

    @Test
    @DisplayName("A handler that answers stops the chain: later handlers and the last stop never run")
    void shortCircuit() {
        AtomicInteger later = new AtomicInteger();
        AtomicInteger lastStopCalls = new AtomicInteger();
        Chain desk = ComplaintDesk.build(List.of(ComplaintDesk.upTo("assistant", 500), counting(later)),
                c -> { lastStopCalls.incrementAndGet(); return HEAD_OFFICE; });
        assertThat(desk.passOn(SMALL)).isEqualTo(new Reply("assistant", "sorted"));
        assertThat(desk.passOn(new Complaint("7783", "dented tin", 500))).as("exactly at the limit").isEqualTo(new Reply("assistant", "sorted"));
        assertThat(later.get()).isZero();
        assertThat(lastStopCalls.get()).isZero();
    }

    @Test
    @DisplayName("Order is behavior: the first handler that answers wins")
    void orderMatters() {
        Chain assistantFirst = ComplaintDesk.build(List.of(ComplaintDesk.upTo("assistant", 500), ComplaintDesk.lateDelivery()), c -> HEAD_OFFICE);
        Chain courierFirst = ComplaintDesk.build(List.of(ComplaintDesk.lateDelivery(), ComplaintDesk.upTo("assistant", 500)), c -> HEAD_OFFICE);
        assertThat(assistantFirst.passOn(LATE_AND_SMALL)).isEqualTo(new Reply("assistant", "sorted"));
        assertThat(courierFirst.passOn(LATE_AND_SMALL)).isEqualTo(new Reply("courier desk", "passed to the courier"));
        assertThat(courierFirst.passOn(SMALL)).as("not late: passed on").isEqualTo(new Reply("assistant", "sorted"));
    }

    @Test
    @DisplayName("Handlers run in list order, once each per complaint, and the chain can be reused")
    void onceEachAndReusable() {
        List<String> order = new ArrayList<>();
        Handler a = (c, next) -> { order.add("a"); return next.passOn(c); };
        Handler b = (c, next) -> { order.add("b"); return next.passOn(c); };
        List<Handler> handlers = new ArrayList<>(List.of(a, b));
        Chain desk = ComplaintDesk.build(handlers, c -> { order.add("end"); return HEAD_OFFICE; });
        handlers.add((c, next) -> new Reply("x", "added after build"));     // must not change the built chain
        desk.passOn(SMALL);
        desk.passOn(SMALL);
        assertThat(order).containsExactly("a", "b", "end", "a", "b", "end");
    }

    @Test
    @DisplayName("An empty chain goes straight to the last stop")
    void emptyChain() {
        assertThat(ComplaintDesk.build(List.of(), c -> HEAD_OFFICE).passOn(SMALL)).isEqualTo(HEAD_OFFICE);
    }
}
