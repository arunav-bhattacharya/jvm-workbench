package workbench.quotes.l01;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelOutboundBuffer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.embedded.EmbeddedChannel;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.ConnectException;
import java.net.InetAddress;
import java.net.Socket;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

@Timeout(30)
class QuoteServerTest {

    // ---- the pipeline, with no socket ----

    private static EmbeddedChannel channel(QuoteSource source) {
        return new EmbeddedChannel(QuotePipeline.handlers(source));
    }

    private static List<String> replies(EmbeddedChannel ch) {
        ch.runPendingTasks();                         // callbacks queued on the channel's loop
        List<String> out = new ArrayList<>();
        for (ByteBuf b; (b = ch.readOutbound()) != null; ) {
            out.add(b.toString(UTF_8));
            b.release();
        }
        return out;
    }

    @Test
    @DisplayName("lines that arrive in pieces are framed, and each reply carries its request id")
    void framesAndAnswers() {
        EmbeddedChannel ch = channel(FakeSource.answering());
        ch.writeInbound(Unpooled.copiedBuffer("7 EUR", UTF_8));
        assertThat(replies(ch)).as("half a line: nothing yet").isEmpty();
        ch.writeInbound(Unpooled.copiedBuffer("USD\n8 GBPUSD\nhello\n", UTF_8));
        assertThat(replies(ch)).containsExactlyInAnyOrder(
                "7 OK EURUSD 1.0842 fake\n", "8 OK GBPUSD 1.0842 fake\n", "ERR bad request\n");
        ch.finishAndReleaseAll();
    }

    @Test
    @DisplayName("QUIT gets BYE, and the connection closes after it")
    void quit() {
        EmbeddedChannel ch = channel(FakeSource.answering());
        ch.writeInbound(Unpooled.copiedBuffer("QUIT\n", UTF_8));
        assertThat(replies(ch)).containsExactly("BYE\n");
        assertThat(ch.isOpen()).isFalse();
    }

    @Test
    @DisplayName("a line longer than MAX_LINE gets an error, then the connection closes")
    void tooLong() {
        EmbeddedChannel ch = channel(FakeSource.answering());
        ch.writeInbound(Unpooled.copiedBuffer("x".repeat(100) + "\n", UTF_8));
        assertThat(replies(ch)).containsExactly("ERR line too long\n");
        assertThat(ch.isOpen()).as("channel open after the error").isFalse();
    }

    @Test
    @DisplayName("reading stops while the channel is not writable, and starts again when it is")
    void writabilityControlsReading() {
        EmbeddedChannel ch = channel(FakeSource.answering());
        ChannelOutboundBuffer out = ch.unsafe().outboundBuffer();
        out.setUserDefinedWritability(1, false);      // what Netty does when the outbound buffer passes the high mark
        ch.runPendingTasks();                          // deliver channelWritabilityChanged
        assertThat(ch.config().isAutoRead()).as("auto-read while not writable").isFalse();
        out.setUserDefinedWritability(1, true);        // drained below the low mark
        ch.runPendingTasks();
        assertThat(ch.config().isAutoRead()).as("auto-read once writable again").isTrue();
        ch.finishAndReleaseAll();
    }

    // ---- the real server, over TCP ----

    private static final class Client implements AutoCloseable {
        final Socket socket;
        final BufferedReader in;

        Client(int port) throws IOException {
            socket = new Socket(InetAddress.getLoopbackAddress(), port);
            socket.setSoTimeout(5_000);
            in = new BufferedReader(new InputStreamReader(socket.getInputStream(), UTF_8));
        }

        void send(String... lines) throws IOException {
            socket.getOutputStream().write((String.join("\n", lines) + "\n").getBytes(UTF_8));   // one write
            socket.getOutputStream().flush();
        }

        String readLine() throws IOException {
            return in.readLine();
        }

        Set<String> readIds(int n) throws IOException {
            Set<String> ids = new HashSet<>();
            for (int i = 0; i < n; i++) ids.add(readLine().split(" ")[0]);
            return ids;
        }

        @Override
        public void close() throws IOException {
            socket.close();
        }
    }

    private static String[] requests(int from, int count) {
        String[] lines = new String[count];
        for (int i = 0; i < count; i++) lines[i] = (from + i) + " EURUSD";
        return lines;
    }

    private static Set<String> ids(int from, int count) {
        Set<String> ids = new HashSet<>();
        for (int i = 0; i < count; i++) ids.add(String.valueOf(from + i));
        return ids;
    }

    /** Hands the loop {@code tasks} empty tasks and counts how many it runs within 5 s. */
    private static int probe(EventLoopGroup group, int tasks) throws InterruptedException {
        CountDownLatch ran = new CountDownLatch(tasks);
        for (int i = 0; i < tasks; i++) group.next().execute(ran::countDown);
        ran.await(5, TimeUnit.SECONDS);
        return tasks - (int) ran.getCount();
    }

    private static void closeQuietly(QuoteServer server) {
        try {
            server.close();
        } catch (RuntimeException notWrittenYet) {
            server.group().shutdownGracefully(0, 1, TimeUnit.SECONDS).awaitUninterruptibly(5, TimeUnit.SECONDS);
        }
    }

    @Test
    @DisplayName("with one event loop, it keeps running other work while 100 quotes are pending")
    void loopStaysFree() throws Exception {
        FakeSource source = FakeSource.holding();
        QuoteServer server = new QuoteServer(1, source);
        List<Client> clients = new ArrayList<>();
        try {
            for (int c = 0; c < 10; c++) {
                Client client = new Client(server.port());
                clients.add(client);
                client.send(requests(c * 10, 10));
            }
            assertThat(source.awaitCalls(100)).as("quotes the server asked for").isEqualTo(100);
            assertThat(probe(server.group(), 50)).as("tasks the loop ran while 100 quotes were pending").isEqualTo(50);
            source.releaseAll();
            for (int c = 0; c < 10; c++) {
                assertThat(clients.get(c).readIds(10)).as("ids answered on connection " + c).isEqualTo(ids(c * 10, 10));
            }
        } finally {
            source.releaseAll();                       // a blocked loop wakes up, so close() can work
            for (Client c : clients) c.close();
            closeQuietly(server);
        }
    }

    @Test
    @DisplayName("a connection with MAX_IN_FLIGHT requests waiting is not read any further")
    void capsWhatOneConnectionHolds() throws Exception {
        FakeSource source = FakeSource.holding();
        QuoteServer server = new QuoteServer(1, source);
        try (Client client = new Client(server.port())) {
            client.send(requests(1, 40));
            assertThat(source.awaitCalls(QuoteProtocol.MAX_IN_FLIGHT)).isGreaterThanOrEqualTo(QuoteProtocol.MAX_IN_FLIGHT);
            probe(server.group(), 3);                  // let the loop finish what it already read
            assertThat(source.calls()).as("requests taken while 16 wait").isEqualTo(QuoteProtocol.MAX_IN_FLIGHT);
            source.releaseAll();
            assertThat(client.readIds(40)).as("every request answered in the end").isEqualTo(ids(1, 40));
        } finally {
            source.releaseAll();
            closeQuietly(server);
        }
    }

    @Test
    @DisplayName("a client that hangs up cancels its pending quotes")
    void hangUpCancels() throws Exception {
        FakeSource source = FakeSource.holding();
        QuoteServer server = new QuoteServer(1, source);
        try {
            Client client = new Client(server.port());
            client.send(requests(1, 5));
            assertThat(source.awaitCalls(5)).isEqualTo(5);
            client.close();
            assertThat(source.awaitCancelled(5)).as("pending quotes cancelled").isEqualTo(5);
        } finally {
            source.releaseAll();
            closeQuietly(server);
        }
    }

    @Test
    @DisplayName("close() stops accepting, closes open connections and stops the loop threads")
    void closeInOrder() throws Exception {
        FakeSource source = FakeSource.holding();
        QuoteServer server = new QuoteServer(1, source);
        int port = server.port();
        try (Client client = new Client(port)) {
            client.send("1 EURUSD");
            assertThat(source.awaitCalls(1)).isEqualTo(1);
            assertTimeoutPreemptively(Duration.ofSeconds(10), server::close, "close() must not hang");
            assertThat(server.group().isTerminated()).as("loop threads stopped").isTrue();
            assertThat(client.readLine()).as("the open connection was closed").isNull();
            assertThat(source.awaitCancelled(1)).as("its pending quote was cancelled").isEqualTo(1);
            assertThatThrownBy(() -> new Socket(InetAddress.getLoopbackAddress(), port).close())
                    .as("a new connection").isInstanceOf(ConnectException.class);
        } finally {
            source.releaseAll();
            closeQuietly(server);
        }
    }
}
