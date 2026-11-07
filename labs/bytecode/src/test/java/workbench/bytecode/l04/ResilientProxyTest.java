package workbench.bytecode.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.bytecode.l04.CardIssuerClient.CardDeclinedException;
import workbench.bytecode.l04.CardIssuerClient.IssuerUnavailableException;

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

    /** A scripted issuer: fails the first N calls of each method, counts every call. */
    static final class FakeIssuer implements CardIssuerClient {
        int authorizeFailures, captureFailures, authorizeCalls, captureCalls;
        boolean decline;

        @Override
        public String authorize(String pan, long amountMinor) throws IssuerUnavailableException {
            authorizeCalls++;
            if (decline) throw new CardDeclinedException("insufficient funds");
            if (authorizeFailures-- > 0) throw new IssuerUnavailableException("issuer down (" + authorizeCalls + ")");
            return "auth-" + pan.substring(pan.length() - 4);
        }

        @Override
        public String capture(String authId) throws IssuerUnavailableException {
            captureCalls++;
            if (captureFailures-- > 0) throw new IssuerUnavailableException("capture timed out (" + captureCalls + ")");
            return "captured " + authId;
        }

        @Override
        public String toString() { return "FakeIssuer"; }
    }

    private static final String PAN = "4111111111111111";
    private final List<String> records = new ArrayList<>();
    private final CallRecorder recorder = (m, attempts, nanos, failed) ->
            records.add(m + " attempts=" + attempts + " " + nanos / 1_000_000 + "ms" + (failed ? " FAILED" : ""));

    /** Every read moves time forward by 5 ms. */
    private static LongSupplier ticking() {
        long[] now = {0};
        return () -> now[0] += 5_000_000;
    }

    private static RetryPolicy retryUnavailable(int maxAttempts) {
        return new RetryPolicy(maxAttempts, Set.of(IssuerUnavailableException.class));
    }

    private CardIssuerClient wrap(FakeIssuer issuer, int maxAttempts) {
        return ResilientProxy.wrap(CardIssuerClient.class, issuer, retryUnavailable(maxAttempts), ticking(), recorder);
    }

    @Test
    @DisplayName("A retryable failure is retried until the call succeeds")
    void retriesUntilSuccess() throws Exception {
        FakeIssuer issuer = new FakeIssuer();
        issuer.authorizeFailures = 2;
        assertThat(wrap(issuer, 3).authorize(PAN, 1_250)).isEqualTo("auth-1111");
        assertThat(issuer.authorizeCalls).isEqualTo(3);
        assertThat(records).containsExactly("CardIssuerClient.authorize attempts=3 5ms");
    }

    @Test
    @DisplayName("After maxAttempts the caller gets the issuer's own exception, not a wrapper")
    void givesUpWithTheOriginalException() {
        FakeIssuer issuer = new FakeIssuer();
        issuer.authorizeFailures = 10;
        CardIssuerClient client = wrap(issuer, 3);
        assertThatThrownBy(() -> client.authorize(PAN, 1_250))
                .isExactlyInstanceOf(IssuerUnavailableException.class)
                .hasMessage("issuer down (3)");
        assertThat(issuer.authorizeCalls).isEqualTo(3);
        assertThat(records).containsExactly("CardIssuerClient.authorize attempts=3 5ms FAILED");
    }

    @Test
    @DisplayName("A failure outside the policy is thrown at once, after one attempt")
    void doesNotRetryADecline() {
        FakeIssuer issuer = new FakeIssuer();
        issuer.decline = true;
        CardIssuerClient client = wrap(issuer, 3);
        assertThatThrownBy(() -> client.authorize(PAN, 1_250))
                .isExactlyInstanceOf(CardDeclinedException.class)
                .hasMessage("insufficient funds");
        assertThat(issuer.authorizeCalls).isEqualTo(1);
        assertThat(records).containsExactly("CardIssuerClient.authorize attempts=1 5ms FAILED");
    }

    @Test
    @DisplayName("A default method runs through the proxy, so each inner call is retried and recorded")
    void defaultMethodInnerCallsAreRetried() throws Exception {
        FakeIssuer issuer = new FakeIssuer();
        issuer.authorizeFailures = 1;
        issuer.captureFailures = 1;
        assertThat(wrap(issuer, 2).authorizeAndCapture(PAN, 1_250)).isEqualTo("captured auth-1111");
        assertThat(issuer.authorizeCalls).isEqualTo(2);
        assertThat(issuer.captureCalls).isEqualTo(2);
        assertThat(records).containsExactly(
                "CardIssuerClient.authorize attempts=2 5ms",
                "CardIssuerClient.capture attempts=2 5ms");
    }

    @Test
    @DisplayName("When a default method's inner call gives up, the default method is not retried (no second authorization)")
    void defaultMethodShellIsNotRetried() {
        FakeIssuer issuer = new FakeIssuer();
        issuer.captureFailures = 10;
        CardIssuerClient client = wrap(issuer, 2);
        assertThatThrownBy(() -> client.authorizeAndCapture(PAN, 1_250))
                .isExactlyInstanceOf(IssuerUnavailableException.class);
        assertThat(issuer.authorizeCalls).as("authorizations sent to the issuer").isEqualTo(1);
        assertThat(issuer.captureCalls).isEqualTo(2);
    }

    @Test
    @DisplayName("equals, hashCode and toString are answered by the proxy: identity, not the target's")
    void objectMethodsUseProxyIdentity() {
        FakeIssuer issuer = new FakeIssuer();
        CardIssuerClient a = wrap(issuer, 3);
        CardIssuerClient b = wrap(issuer, 3);
        assertThat(a.equals(a)).isTrue();
        assertThat(a.equals(b)).isFalse();
        assertThat(a.equals(issuer)).isFalse();
        assertThat(a.hashCode()).isEqualTo(System.identityHashCode(a));
        assertThat(a.toString()).isEqualTo("Resilient[FakeIssuer]");
        List<CardIssuerClient> listeners = new ArrayList<>(List.of(a, b));
        assertThat(listeners.remove(a)).as("ArrayList.remove uses equals").isTrue();
        assertThat(new HashSet<>(listeners)).containsExactly(b);
        assertThat(records).as("Object methods are not recorded").isEmpty();
        assertThat(issuer.authorizeCalls + issuer.captureCalls).isZero();
    }

    @Test
    @DisplayName("Every wrap returns a final $Proxy class that implements exactly CardIssuerClient, generated once")
    void proxyAnatomy() {
        CardIssuerClient a = wrap(new FakeIssuer(), 1);
        CardIssuerClient b = wrap(new FakeIssuer(), 5);
        Class<?> pc = a.getClass();
        assertThat(Proxy.isProxyClass(pc)).isTrue();
        assertThat(pc.getSimpleName()).startsWith("$Proxy");
        assertThat(Modifier.isFinal(pc.getModifiers())).isTrue();
        assertThat(pc.getInterfaces()).containsExactly(CardIssuerClient.class);
        assertThat(b.getClass()).isSameAs(pc);
    }
}
