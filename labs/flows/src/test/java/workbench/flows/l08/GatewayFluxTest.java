package workbench.flows.l08;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.time.Duration;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

// A Java caller: it sees only GatewayApi, GatewayEvent and Reactor types, never a Flow.
class GatewayFluxTest {

    private final GatewayEvent authorized = new GatewayEvent("p-42", "AUTHORIZED");
    private final GatewayEvent captured = new GatewayEvent("p-42", "CAPTURED");
    private final GatewayEvent settled = new GatewayEvent("p-42", "SETTLED");

    @Test
    @DisplayName("Java gets the gateway events as a Flux, and take(2) unregisters the listener")
    void takeTwo() {
        FakeGateway gw = new FakeGateway();
        StepVerifier.create(new GatewayApi(gw).eventsFlux().take(2))
                .then(() -> { gw.fire(authorized); gw.fire(captured); gw.fire(settled); })
                .expectNext(authorized, captured)
                .expectComplete()
                .verify(Duration.ofSeconds(5));
        assertThat(gw.getListenerCount()).as("listeners after take(2)").isZero();
    }

    @Test
    @DisplayName("an SDK error reaches the Java subscriber as onError")
    void error() {
        FakeGateway gw = new FakeGateway();
        StepVerifier.create(new GatewayApi(gw).eventsFlux())
                .then(() -> gw.fail(new IOException("gateway connection lost")))
                .expectErrorMatches(e -> e instanceof IOException && e.getMessage().equals("gateway connection lost"))
                .verify(Duration.ofSeconds(5));
        assertThat(gw.getListenerCount()).isZero();
    }

    @Test
    @DisplayName("the listener is registered at the first request(n), not at subscribe")
    void registersOnFirstRequest() {
        FakeGateway gw = new FakeGateway();
        StepVerifier.create(new GatewayApi(gw).eventsFlux(), 0)   // subscribe with no demand
                .then(() -> assertThat(gw.getListenerCount()).as("listeners before any request").isZero())
                .thenRequest(1)
                .then(() -> {
                    assertThat(gw.getListenerCount()).as("listeners after request(1)").isEqualTo(1);
                    gw.fire(authorized);
                })
                .expectNext(authorized)
                .thenCancel()
                .verify(Duration.ofSeconds(5));
        assertThat(gw.getListenerCount()).as("listeners after cancel").isZero();
    }
}
