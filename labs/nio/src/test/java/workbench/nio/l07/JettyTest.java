package workbench.nio.l07;

import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.util.thread.Invocable;
import org.eclipse.jetty.util.thread.QueuedThreadPool;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

@Timeout(30)
class JettyTest {
    static final HttpClient CLIENT = HttpClient.newBuilder()
            .proxy(HttpClient.Builder.NO_PROXY).version(HttpClient.Version.HTTP_1_1).build();

    static URI uri(Server server) {
        return URI.create("http://127.0.0.1:" + PaymentServer.port(server) + "/");
    }

    /** n concurrent GETs; returns the bodies. */
    static List<String> load(Server server, int n) throws Exception {
        List<CompletableFuture<HttpResponse<String>>> calls = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            calls.add(CLIENT.sendAsync(HttpRequest.newBuilder(uri(server)).build(), HttpResponse.BodyHandlers.ofString()));
        }
        List<String> bodies = new ArrayList<>();
        for (var call : calls) {
            HttpResponse<String> r = call.get(20, TimeUnit.SECONDS);
            assertThat(r.statusCode()).isEqualTo(200);
            bodies.add(r.body());
        }
        return bodies;
    }

    @Test
    @DisplayName("handlers declare their invocation type: the ledger blocks, status and echo don't")
    void invocationTypes() {
        assertThat(new LedgerHandler(0).getInvocationType()).isEqualTo(Invocable.InvocationType.BLOCKING);
        assertThat(new StatusHandler().getInvocationType()).isEqualTo(Invocable.InvocationType.NON_BLOCKING);
        assertThat(new EchoHandler().getInvocationType()).isEqualTo(Invocable.InvocationType.NON_BLOCKING);
    }

    @Test
    @DisplayName("the echo handler reads the body asynchronously and completes the callback later")
    void asyncEcho() throws Exception {
        Server server = PaymentServer.start(new QueuedThreadPool(), new EchoHandler());
        try {
            HttpResponse<String> r = CLIENT.send(HttpRequest.newBuilder(uri(server))
                    .POST(HttpRequest.BodyPublishers.ofString("auth-42")).build(), HttpResponse.BodyHandlers.ofString());
            assertThat(r.statusCode()).isEqualTo(200);
            assertThat(r.body()).isEqualTo("echo: auth-42");
        } finally {
            server.stop();
        }
    }

    @Test
    @DisplayName("on a 12-thread platform pool, at most a handful of 40 blocking requests run at once")
    void platformPoolCapsConcurrency() throws Exception {
        LedgerHandler ledger = new LedgerHandler(300);
        Server server = PaymentServer.start(new QueuedThreadPool(12), ledger);
        try {
            List<String> bodies = load(server, 40);
            assertThat(bodies).allMatch(b -> b.startsWith("balance=12500") && b.contains("virtual=false"));
            assertThat(ledger.maxConcurrent()).as("requests in the handler at once").isLessThanOrEqualTo(12);
        } finally {
            server.stop();
        }
    }

    @Test
    @DisplayName("with a virtual threads executor, the 40 blocking requests run on virtual threads, all at once")
    void virtualThreadsLiftTheCap() throws Exception {
        LedgerHandler ledger = new LedgerHandler(300);
        Server server = PaymentServer.start(PaymentServer.virtualQueuedThreadPool(12), ledger);
        try {
            List<String> bodies = load(server, 40);
            assertThat(bodies).allMatch(b -> b.contains("thread=ledger-vt-") && b.contains("virtual=true"));
            assertThat(ledger.maxConcurrent()).as("requests in the handler at once").isGreaterThanOrEqualTo(30);
        } finally {
            server.stop();
        }
    }

    @Test
    @DisplayName("a NON_BLOCKING handler stays on a platform thread even when virtual threads are enabled")
    void nonBlockingStaysOnPlatformThreads() throws Exception {
        Server server = PaymentServer.start(PaymentServer.virtualQueuedThreadPool(12), new StatusHandler());
        try {
            for (String body : load(server, 5)) {
                assertThat(body).startsWith("UP").contains("virtual=false");
            }
        } finally {
            server.stop();
        }
    }
}
