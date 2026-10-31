package workbench.patterns.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l05.FeeCalculator.Payment;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeoutException;
import java.util.function.LongSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DecoratorProxyTest {

    // ---- decorator chain ----

    private static final FeeCalculator STANDARD =
            FeeCalculator.percent(290).plusFixed(30).crossBorder("DE", 100).cappedAt(500);

    @Test
    @DisplayName("percent takes basis points of the amount, with integer division")
    void percent() {
        assertThat(FeeCalculator.percent(290).feeMinor(new Payment(10_000, "DE"))).isEqualTo(290);
        assertThat(FeeCalculator.percent(150).feeMinor(new Payment(999, "DE"))).isEqualTo(14);
    }

    @Test
    @DisplayName("Domestic 100.00 EUR: 2.9% + 0.30 = 3.20")
    void domestic() {
        assertThat(STANDARD.feeMinor(new Payment(10_000, "DE"))).isEqualTo(320);
    }

    @Test
    @DisplayName("Cross-border 100.00 EUR: 3.20 + 1% = 4.20")
    void crossBorder() {
        assertThat(STANDARD.feeMinor(new Payment(10_000, "FR"))).isEqualTo(420);
    }

    @Test
    @DisplayName("Cross-border 1,000.00 EUR hits the 5.00 cap")
    void capped() {
        assertThat(STANDARD.feeMinor(new Payment(100_000, "FR"))).isEqualTo(500);
    }

    @Test
    @DisplayName("Order matters: capping before the surcharge gives 15.00")
    void orderMatters() {
        FeeCalculator capFirst = FeeCalculator.percent(290).plusFixed(30).cappedAt(500).crossBorder("DE", 100);
        assertThat(capFirst.feeMinor(new Payment(100_000, "FR"))).isEqualTo(1_500);
    }

    @Test
    @DisplayName("Each decorator returns a new calculator and leaves the one it wraps unchanged")
    void decoratorsDontMutate() {
        FeeCalculator base = FeeCalculator.percent(290);
        FeeCalculator withFixed = base.plusFixed(30);
        assertThat(base.feeMinor(new Payment(10_000, "DE"))).isEqualTo(290);
        assertThat(withFixed.feeMinor(new Payment(10_000, "DE"))).isEqualTo(320);
    }

    // ---- timing proxy ----

    public interface IssuerClient {
        String authorize(String pan, long amountMinor) throws TimeoutException;
        String authorizeTwice(String pan, long amountMinor) throws TimeoutException;
    }

    static final class RealIssuer implements IssuerClient {
        int calls;
        @Override public String authorize(String pan, long amountMinor) throws TimeoutException {
            calls++;
            if (amountMinor < 0) throw new IllegalArgumentException("negative amount");
            if (pan.startsWith("0000")) throw new TimeoutException("issuer took longer than 120 ms");
            return "A-" + pan.substring(pan.length() - 4);
        }
        @Override public String authorizeTwice(String pan, long amountMinor) throws TimeoutException {
            authorize(pan, amountMinor);                 // self-invocation: this.authorize, not the proxy
            return authorize(pan, amountMinor);
        }
        @Override public String toString() { return "RealIssuer"; }
    }

    /** A fake clock: every read moves time forward by 7 ms. */
    private static LongSupplier ticking() {
        long[] now = {0};
        return () -> now[0] += 7_000_000;
    }

    private final List<String> records = new ArrayList<>();
    private final TimingProxy.MetricsSink sink = (name, nanos, failed) -> records.add(name + " " + nanos / 1_000_000 + "ms" + (failed ? " FAILED" : ""));

    @Test
    @DisplayName("The proxy implements the interface and forwards arguments and results")
    void forwards() throws Exception {
        RealIssuer real = new RealIssuer();
        IssuerClient proxy = TimingProxy.wrap(IssuerClient.class, real, ticking(), sink);
        assertThat(Proxy.isProxyClass(proxy.getClass())).isTrue();
        assertThat(proxy.authorize("4111111111111111", 1_250)).isEqualTo("A-1111");
        assertThat(real.calls).isEqualTo(1);
    }

    @Test
    @DisplayName("Each call is reported as Interface.method with the time between two clock reads")
    void reportsTiming() throws Exception {
        IssuerClient proxy = TimingProxy.wrap(IssuerClient.class, new RealIssuer(), ticking(), sink);
        proxy.authorize("4111111111111111", 1_250);
        proxy.authorize("4242424242424242", 990);
        assertThat(records).containsExactly("IssuerClient.authorize 7ms", "IssuerClient.authorize 7ms");
    }

    @Test
    @DisplayName("A runtime exception from the target reaches the caller unwrapped, and is reported as failed")
    void runtimeExceptionUnwrapped() {
        IssuerClient proxy = TimingProxy.wrap(IssuerClient.class, new RealIssuer(), ticking(), sink);
        assertThatThrownBy(() -> proxy.authorize("4111111111111111", -1))
                .isExactlyInstanceOf(IllegalArgumentException.class)
                .hasMessage("negative amount");
        assertThat(records).containsExactly("IssuerClient.authorize 7ms FAILED");
    }

    @Test
    @DisplayName("A checked exception the interface declares reaches the caller as itself")
    void checkedExceptionUnwrapped() {
        IssuerClient proxy = TimingProxy.wrap(IssuerClient.class, new RealIssuer(), ticking(), sink);
        assertThatThrownBy(() -> proxy.authorize("0000111122223333", 100))
                .isExactlyInstanceOf(TimeoutException.class);
        assertThat(records).containsExactly("IssuerClient.authorize 7ms FAILED");
    }

    @Test
    @DisplayName("toString, equals and hashCode are forwarded but not timed")
    void objectMethodsNotTimed() {
        IssuerClient proxy = TimingProxy.wrap(IssuerClient.class, new RealIssuer(), ticking(), sink);
        assertThat(proxy.toString()).isEqualTo("RealIssuer");
        proxy.hashCode();
        assertThat(records).isEmpty();
    }

    @Test
    @DisplayName("Self-invocation skips the proxy: authorizeTwice is timed, its inner calls are not")
    void selfInvocationBypassesProxy() throws Exception {
        RealIssuer real = new RealIssuer();
        IssuerClient proxy = TimingProxy.wrap(IssuerClient.class, real, ticking(), sink);
        proxy.authorizeTwice("4111111111111111", 100);
        assertThat(real.calls).isEqualTo(2);
        assertThat(records).containsExactly("IssuerClient.authorizeTwice 7ms");
    }
}
