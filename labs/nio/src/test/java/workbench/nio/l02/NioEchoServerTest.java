package workbench.nio.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.Random;

import static org.assertj.core.api.Assertions.assertThat;

@Timeout(20)
class NioEchoServerTest {

    static Socket connect(int port) throws IOException {
        Socket s = new Socket();
        s.setReceiveBufferSize(4 * 1024);   // a small client buffer makes the server see partial writes
        s.setSoTimeout(5_000);             // a broken server fails the test instead of hanging it
        s.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), port));
        return s;
    }

    static byte[] readToEof(InputStream in) throws IOException {
        ByteArrayOutputStream got = new ByteArrayOutputStream();
        byte[] chunk = new byte[8 * 1024];
        int n;
        while ((n = in.read(chunk)) >= 0) got.write(chunk, 0, n);
        return got.toByteArray();
    }

    @Test
    @DisplayName("echoes 4 MiB byte for byte to a client with a 4 KiB receive buffer, then closes")
    void echoesEverything() throws Exception {
        byte[] payload = new byte[4 * 1024 * 1024];
        new Random(42).nextBytes(payload);
        try (NioEchoServer server = new NioEchoServer(); Socket client = connect(server.port())) {
            // write and read at the same time, or both sides' buffers fill up and the echo stalls
            Thread writer = new Thread(() -> {
                try {
                    OutputStream out = client.getOutputStream();
                    out.write(payload);
                    client.shutdownOutput();   // half-close: "no more bytes from me"
                } catch (IOException ignored) { }
            });
            writer.start();
            byte[] echoed = readToEof(client.getInputStream());
            writer.join();
            assertThat(echoed.length).as("bytes echoed").isEqualTo(payload.length);
            assertThat(echoed).as("echoed bytes match").isEqualTo(payload);
        }
    }

    @Test
    @DisplayName("after a half-close the server sends what it still holds, and only then closes")
    void flushesBeforeClosing() throws Exception {
        byte[] payload = new byte[1024 * 1024];
        new Random(7).nextBytes(payload);
        try (NioEchoServer server = new NioEchoServer(); Socket client = connect(server.port())) {
            Thread writer = new Thread(() -> {
                try {
                    client.getOutputStream().write(payload);
                    client.shutdownOutput();       // the server sees EOF while it still holds unsent bytes
                } catch (IOException ignored) { }
            });
            writer.start();
            // a slow reader: the server's buffer stays full, so EOF arrives before the last bytes leave
            ByteArrayOutputStream got = new ByteArrayOutputStream();
            InputStream in = client.getInputStream();
            byte[] chunk = new byte[8 * 1024];
            int n;
            while ((n = in.read(chunk)) >= 0) {
                got.write(chunk, 0, n);
                Thread.sleep(1);
            }
            writer.join();
            assertThat(got.size()).as("bytes before EOF").isEqualTo(payload.length);
            assertThat(got.toByteArray()).isEqualTo(payload);
        }
    }

    @Test
    @DisplayName("an idle connection does not wake the selector")
    void idleConnectionDoesNotSpin() throws Exception {
        try (NioEchoServer server = new NioEchoServer(); Socket client = connect(server.port())) {
            client.getOutputStream().write("ping".getBytes());
            assertThat(client.getInputStream().readNBytes(4)).isEqualTo("ping".getBytes());
            Thread.sleep(100);                 // let the loop settle after the echo
            long before = server.wakeups();
            Thread.sleep(300);                 // the connection is open and idle
            long during = server.wakeups() - before;
            assertThat(during).as("select() wakeups in 300 ms of idle").isLessThan(10);
        }
    }
}
