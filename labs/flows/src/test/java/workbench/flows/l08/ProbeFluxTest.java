package workbench.flows.l08;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.time.Duration;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

// A Java caller: it sees only ProbeApi, ProbeReading and Reactor types, never a Flow.
class ProbeFluxTest {

    private final ProbeReading first = new ProbeReading(1, 61);
    private final ProbeReading second = new ProbeReading(2, 63);
    private final ProbeReading third = new ProbeReading(3, 65);

    @Test
    @DisplayName("Java gets the probe's readings as a Flux, and take(2) unregisters the listener")
    void takeTwo() {
        FakeProbe probe = new FakeProbe();
        StepVerifier.create(new ProbeApi(probe).readingsFlux().take(2))
                .then(() -> { probe.fire(first); probe.fire(second); probe.fire(third); })
                .expectNext(first, second)
                .expectComplete()
                .verify(Duration.ofSeconds(5));
        assertThat(probe.getListenerCount()).as("listeners after take(2)").isZero();
    }

    @Test
    @DisplayName("a probe error reaches the Java subscriber as onError")
    void error() {
        FakeProbe probe = new FakeProbe();
        StepVerifier.create(new ProbeApi(probe).readingsFlux())
                .then(() -> probe.fail(new IOException("probe connection lost")))
                .expectErrorMatches(e -> e instanceof IOException && e.getMessage().equals("probe connection lost"))
                .verify(Duration.ofSeconds(5));
        assertThat(probe.getListenerCount()).isZero();
    }

    @Test
    @DisplayName("the listener is registered at the first request(n), not at subscribe")
    void registersOnFirstRequest() {
        FakeProbe probe = new FakeProbe();
        StepVerifier.create(new ProbeApi(probe).readingsFlux(), 0)   // subscribe with no demand
                .then(() -> assertThat(probe.getListenerCount()).as("listeners before any request").isZero())
                .thenRequest(1)
                .then(() -> {
                    assertThat(probe.getListenerCount()).as("listeners after request(1)").isEqualTo(1);
                    probe.fire(first);
                })
                .expectNext(first)
                .thenCancel()
                .verify(Duration.ofSeconds(5));
        assertThat(probe.getListenerCount()).as("listeners after cancel").isZero();
    }
}
