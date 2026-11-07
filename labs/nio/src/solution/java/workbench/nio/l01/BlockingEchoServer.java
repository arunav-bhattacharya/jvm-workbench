package workbench.nio.l01;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicInteger;

import static java.nio.charset.StandardCharsets.UTF_8;

public final class BlockingEchoServer implements AutoCloseable {
    private final ServerSocket server;
    private final ExecutorService handlers;
    private final Set<Socket> open = ConcurrentHashMap.newKeySet();
    private final AtomicInteger inHandler = new AtomicInteger();

    public BlockingEchoServer(ExecutorService handlers) throws IOException {
        this.handlers = handlers;
        this.server = new ServerSocket(0, 1_000, InetAddress.getLoopbackAddress());
        Thread acceptor = new Thread(this::acceptLoop, "echo-acceptor");
        acceptor.setDaemon(true);
        acceptor.start();
    }

    public int port() {
        return server.getLocalPort();
    }

    public int connectionsInHandler() {
        return inHandler.get();
    }

    private void acceptLoop() {
        while (!server.isClosed()) {
            try {
                Socket socket = server.accept();          // blocks until a client connects
                open.add(socket);
                handlers.execute(() -> handle(socket));   // the executor decides who serves it, and when
            } catch (IOException | RejectedExecutionException e) {
                return;                                   // server closed: stop accepting
            }
        }
    }

    private void handle(Socket socket) {
        inHandler.incrementAndGet();
        try (socket;
             BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), UTF_8))) {
            OutputStream out = socket.getOutputStream();
            String line;
            while ((line = in.readLine()) != null) {      // the thread waits here, doing nothing, between lines
                out.write((line + "\n").getBytes(UTF_8));
                out.flush();
            }
        } catch (IOException e) {
            // client vanished or server closing: nothing to answer
        } finally {
            open.remove(socket);
            inHandler.decrementAndGet();
        }
    }

    @Override
    public void close() throws IOException {
        server.close();
        for (Socket s : open) {
            try { s.close(); } catch (IOException ignored) { }
        }
        handlers.shutdownNow();
    }
}
