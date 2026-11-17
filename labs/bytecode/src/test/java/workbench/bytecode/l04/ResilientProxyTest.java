package workbench.bytecode.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.bytecode.l04.SeatDesk.DeskUnavailableException;
import workbench.bytecode.l04.SeatDesk.SoldOutException;

import java.lang.reflect.Modifier;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.LongSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ResilientProxyTest {

    /** A scripted desk: fails the first N calls of each method, counts every call. */
    static final class FakeDesk implements SeatDesk {
        int holdFailures, confirmFailures, holdCalls, confirmCalls;
        boolean soldOut;

        @Override
        public String hold(String show, String guest) throws DeskUnavailableException {
            holdCalls++;
            if (soldOut) throw new SoldOutException("no seats left for " + show);
            if (holdFailures-- > 0) throw new DeskUnavailableException("desk not answering (" + holdCalls + ")");
            return "hold-" + show.toLowerCase();
        }

        @Override
        public String confirm(String holdId) throws DeskUnavailableException {
            confirmCalls++;
            if (confirmFailures-- > 0) throw new DeskUnavailableException("confirm timed out (" + confirmCalls + ")");
            return "confirmed " + holdId;
        }

        @Override
        public String toString() { return "FakeDesk"; }
    }

    private final List<String> records = new ArrayList<>();
    private final CallRecorder recorder = (m, attempts, nanos, failed) ->
            records.add(m + " attempts=" + attempts + " " + nanos / 1_000_000 + "ms" + (failed ? " FAILED" : ""));

    /** Every read moves time forward by 5 ms. */
    private static LongSupplier ticking() {
        long[] now = {0};
        return () -> now[0] += 5_000_000;
    }

    private static RetryPolicy retryUnavailable(int maxAttempts) {
        return new RetryPolicy(maxAttempts, Set.of(DeskUnavailableException.class));
    }

    private SeatDesk wrap(FakeDesk desk, int maxAttempts) {
        return ResilientProxy.wrap(SeatDesk.class, desk, retryUnavailable(maxAttempts), ticking(), recorder);
    }

    @Test
    @DisplayName("A retryable failure is retried until the call succeeds")
    void retriesUntilSuccess() throws Exception {
        FakeDesk desk = new FakeDesk();
        desk.holdFailures = 2;
        assertThat(wrap(desk, 3).hold("Hamlet", "ana")).isEqualTo("hold-hamlet");
        assertThat(desk.holdCalls).isEqualTo(3);
        assertThat(records).containsExactly("SeatDesk.hold attempts=3 5ms");
    }

    @Test
    @DisplayName("After maxAttempts the caller gets the desk's own exception, not a wrapper")
    void givesUpWithTheOriginalException() {
        FakeDesk desk = new FakeDesk();
        desk.holdFailures = 10;
        SeatDesk client = wrap(desk, 3);
        assertThatThrownBy(() -> client.hold("Hamlet", "ana"))
                .isExactlyInstanceOf(DeskUnavailableException.class)
                .hasMessage("desk not answering (3)");
        assertThat(desk.holdCalls).isEqualTo(3);
        assertThat(records).containsExactly("SeatDesk.hold attempts=3 5ms FAILED");
    }

    @Test
    @DisplayName("A failure outside the policy is thrown at once, after one attempt")
    void doesNotRetrySoldOut() {
        FakeDesk desk = new FakeDesk();
        desk.soldOut = true;
        SeatDesk client = wrap(desk, 3);
        assertThatThrownBy(() -> client.hold("Hamlet", "ana"))
                .isExactlyInstanceOf(SoldOutException.class)
                .hasMessage("no seats left for Hamlet");
        assertThat(desk.holdCalls).isEqualTo(1);
        assertThat(records).containsExactly("SeatDesk.hold attempts=1 5ms FAILED");
    }

    @Test
    @DisplayName("A default method runs through the proxy, so each inner call is retried and recorded")
    void defaultMethodInnerCallsAreRetried() throws Exception {
        FakeDesk desk = new FakeDesk();
        desk.holdFailures = 1;
        desk.confirmFailures = 1;
        assertThat(wrap(desk, 2).holdAndConfirm("Hamlet", "ana")).isEqualTo("confirmed hold-hamlet");
        assertThat(desk.holdCalls).isEqualTo(2);
        assertThat(desk.confirmCalls).isEqualTo(2);
        assertThat(records).containsExactly(
                "SeatDesk.hold attempts=2 5ms",
                "SeatDesk.confirm attempts=2 5ms");
    }

    @Test
    @DisplayName("When a default method's inner call gives up, the default method is not retried (no second hold)")
    void defaultMethodShellIsNotRetried() {
        FakeDesk desk = new FakeDesk();
        desk.confirmFailures = 10;
        SeatDesk client = wrap(desk, 2);
        assertThatThrownBy(() -> client.holdAndConfirm("Hamlet", "ana"))
                .isExactlyInstanceOf(DeskUnavailableException.class);
        assertThat(desk.holdCalls).as("holds sent to the desk").isEqualTo(1);
        assertThat(desk.confirmCalls).isEqualTo(2);
    }

    @Test
    @DisplayName("equals, hashCode and toString are answered by the proxy: identity, not the target's")
    void objectMethodsUseProxyIdentity() {
        FakeDesk desk = new FakeDesk();
        SeatDesk a = wrap(desk, 3);
        SeatDesk b = wrap(desk, 3);
        assertThat(a.equals(a)).isTrue();
        assertThat(a.equals(b)).isFalse();
        assertThat(a.equals(desk)).isFalse();
        assertThat(a.hashCode()).isEqualTo(System.identityHashCode(a));
        assertThat(a.toString()).isEqualTo("Resilient[FakeDesk]");
        List<SeatDesk> listeners = new ArrayList<>(List.of(a, b));
        assertThat(listeners.remove(a)).as("ArrayList.remove uses equals").isTrue();
        assertThat(new HashSet<>(listeners)).containsExactly(b);
        assertThat(records).as("Object methods are not recorded").isEmpty();
        assertThat(desk.holdCalls + desk.confirmCalls).isZero();
    }

    @Test
    @DisplayName("Every wrap returns a final $Proxy class that implements exactly SeatDesk, generated once")
    void proxyAnatomy() {
        SeatDesk a = wrap(new FakeDesk(), 1);
        SeatDesk b = wrap(new FakeDesk(), 5);
        Class<?> pc = a.getClass();
        assertThat(Proxy.isProxyClass(pc)).isTrue();
        assertThat(pc.getSimpleName()).startsWith("$Proxy");
        assertThat(Modifier.isFinal(pc.getModifiers())).isTrue();
        assertThat(pc.getInterfaces()).containsExactly(SeatDesk.class);
        assertThat(b.getClass()).isSameAs(pc);
    }
}
