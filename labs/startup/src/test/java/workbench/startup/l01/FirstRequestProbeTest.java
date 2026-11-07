package workbench.startup.l01;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.URI;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class FirstRequestProbeTest {
    // no proxy: the probe must talk straight to the local port
    private final HttpClient client = HttpClient.newBuilder()
            .proxy(HttpClient.Builder.NO_PROXY)
            .connectTimeout(Duration.ofSeconds(2))
            .build();
    private HttpServer server;

    @AfterEach
    void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    /** A service that answers 503 while it "starts", then 200. */
    private URI serviceReadyAfter(int notReadyAnswers) throws Exception {
        AtomicInteger calls = new AtomicInteger();
        server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        server.createContext("/ready", exchange -> {
            int status = calls.incrementAndGet() <= notReadyAnswers ? 503 : 200;
            exchange.sendResponseHeaders(status, -1);
            exchange.close();
        });
        server.start();
        return URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/ready");
    }

    /** A port that nothing listens on. */
    private static int freePort() throws Exception {
        try (ServerSocket s = new ServerSocket(0, 1, InetAddress.getLoopbackAddress())) {
            return s.getLocalPort();
        }
    }

    @Test
    @DisplayName("keeps polling through 503s and stops at the first 200")
    void pollsUntilReady() throws Exception {
        URI uri = serviceReadyAfter(3);
        FirstRequestProbe.Result r = FirstRequestProbe.await(client, uri, 20, Duration.ofMillis(5));
        assertThat(r.outcomes()).containsExactly("503", "503", "503", "200");
        assertThat(r.ready()).isTrue();
    }

    @Test
    @DisplayName("a service that is up at once needs one attempt")
    void readyAtOnce() throws Exception {
        URI uri = serviceReadyAfter(0);
        FirstRequestProbe.Result r = FirstRequestProbe.await(client, uri, 20, Duration.ofMillis(5));
        assertThat(r.outcomes()).containsExactly("200");
    }

    @Test
    @DisplayName("a refused connection means not up yet: it is recorded, not thrown")
    void refusedIsNotReady() throws Exception {
        URI uri = URI.create("http://127.0.0.1:" + freePort() + "/ready");
        FirstRequestProbe.Result r = FirstRequestProbe.await(client, uri, 3, Duration.ofMillis(5));
        assertThat(r.outcomes()).containsExactly("refused", "refused", "refused");
        assertThat(r.ready()).isFalse();
    }

    @Test
    @DisplayName("gives up after maxAttempts when the service never gets ready")
    void givesUp() throws Exception {
        URI uri = serviceReadyAfter(100);
        FirstRequestProbe.Result r = FirstRequestProbe.await(client, uri, 4, Duration.ofMillis(5));
        assertThat(r.outcomes()).containsExactly("503", "503", "503", "503");
        assertThat(r.ready()).isFalse();
    }
}
