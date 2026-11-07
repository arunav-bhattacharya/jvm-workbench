package workbench.nio.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.function.IntSupplier;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@Timeout(20)
class BlockingEchoServerTest {

    /** A client that sends one line, reads the echo, and then stays connected and idle. */
    static final class Client implements AutoCloseable {
        final Socket socket;
        final BufferedReader in;

        Client(int port) throws IOException {
            socket = new Socket(InetAddress.getLoopbackAddress(), port);
            socket.setSoTimeout(3_000);   // a stub that never answers fails fast instead of hanging
            in = new BufferedReader(new InputStreamReader(socket.getInputStream(), UTF_8));
        }

        void send(String line) throws IOException {
            socket.getOutputStream().write((line + "\n").getBytes(UTF_8));
            socket.getOutputStream().flush();
        }

        String roundTrip(String line) throws IOException {
            send(line);
            return in.readLine();
        }

        @Override
        public void close() throws IOException {
            socket.close();
        }
    }

    static void eventually(IntSupplier actual, int expected) throws InterruptedException {
        long deadline = System.nanoTime() + 5_000_000_000L;
        while (actual.getAsInt() != expected && System.nanoTime() < deadline) Thread.sleep(10);
        assertThat(actual.getAsInt()).isEqualTo(expected);
    }

    @Test
    @DisplayName("echoes each line back, in order")
    void echoesLines() throws Exception {
        try (BlockingEchoServer server = new BlockingEchoServer(Executors.newCachedThreadPool());
             Client c = new Client(server.port())) {
            assertThat(c.roundTrip("auth-1")).isEqualTo("auth-1");
            assertThat(c.roundTrip("auth-2 amount=12.50")).isEqualTo("auth-2 amount=12.50");
        }
    }

    @Test
    @DisplayName("thread per connection: 50 idle clients hold 50 threads, and closing them frees the threads")
    void idleClientsHoldThreads() throws Exception {
        ExecutorService pool = Executors.newCachedThreadPool();
        try (BlockingEchoServer server = new BlockingEchoServer(pool)) {
            List<Client> clients = new ArrayList<>();
            for (int i = 0; i < 50; i++) {
                Client c = new Client(server.port());
                assertThat(c.roundTrip("hello " + i)).isEqualTo("hello " + i);
                clients.add(c);                     // connected, now idle: its handler sits in readLine()
            }
            assertThat(server.connectionsInHandler()).isEqualTo(50);
            assertThat(((ThreadPoolExecutor) pool).getPoolSize()).as("threads in the pool").isEqualTo(50);
            for (Client c : clients) c.close();
            eventually(server::connectionsInHandler, 0);
        }
    }

    @Test
    @DisplayName("a fixed pool of 4 serves 4 connections; the 5th waits until one leaves")
    void fixedPoolCapsConnections() throws Exception {
        try (BlockingEchoServer server = new BlockingEchoServer(Executors.newFixedThreadPool(4))) {
            List<Client> first = new ArrayList<>();
            for (int i = 0; i < 4; i++) {
                Client c = new Client(server.port());
                assertThat(c.roundTrip("c" + i)).isEqualTo("c" + i);
                first.add(c);
            }
            try (Client fifth = new Client(server.port())) {
                fifth.send("fifth");
                fifth.socket.setSoTimeout(300);
                assertThatThrownBy(fifth.in::readLine)
                        .as("no thread is free, so nobody reads the fifth client's line")
                        .isInstanceOf(SocketTimeoutException.class);
                first.get(0).close();               // one thread comes back to the pool
                fifth.socket.setSoTimeout(5_000);
                assertThat(fifth.in.readLine()).isEqualTo("fifth");
            }
            for (Client c : first) c.close();
        }
    }

    @Test
    @DisplayName("virtual threads: 500 idle clients cost only a handful of platform threads")
    void virtualThreadsScale() throws Exception {
        int before = ManagementFactory.getThreadMXBean().getThreadCount();   // counts platform threads only
        try (BlockingEchoServer server = new BlockingEchoServer(Executors.newVirtualThreadPerTaskExecutor())) {
            List<Client> clients = new ArrayList<>();
            try {
                for (int i = 0; i < 500; i++) {
                    Client c = new Client(server.port());
                    assertThat(c.roundTrip("v" + i)).isEqualTo("v" + i);
                    clients.add(c);
                }
                assertThat(server.connectionsInHandler()).isEqualTo(500);
                int after = ManagementFactory.getThreadMXBean().getThreadCount();
                assertThat(after - before).as("new platform threads for 500 blocked readers").isLessThan(50);
            } finally {
                for (Client c : clients) c.close();
            }
        }
    }
}
