package workbench.nio.l01;

import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A line echo server built the classic way: one blocking accept loop, and one task per
 * connection that blocks in {@code read()} until the client sends a line.
 *
 * <p>The constructor binds 127.0.0.1 on a free port and starts the accept loop on its own
 * thread. Every accepted connection is handed to {@code handlers}, so the executor you pass
 * decides how many connections can be served at once.
 *
 * <p>Your job: write {@link #acceptLoop()} and {@link #handle(Socket)}.
 */
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

    /** The port the server listens on. */
    public int port() {
        return server.getLocalPort();
    }

    /** How many connections are inside {@link #handle(Socket)} right now. */
    public int connectionsInHandler() {
        return inHandler.get();
    }

    /**
     * Accept connections until the server socket is closed. For each one: remember it in
     * {@code open} (so {@link #close()} can close it) and submit {@code handle(socket)} to
     * {@code handlers}. When {@code accept()} throws because the server was closed, return.
     */
    private void acceptLoop() {
        throw new UnsupportedOperationException("TODO: accept, remember the socket, submit handle(socket)");
    }

    /**
     * Serve one connection: increment {@code inHandler}, then read lines (UTF-8) and write each
     * one back followed by {@code \n}, flushing after every line. When the client closes its side
     * ({@code readLine()} returns null) or the socket fails, close the socket, remove it from
     * {@code open} and decrement {@code inHandler}. Use try/finally so the count always goes down.
     */
    private void handle(Socket socket) {
        throw new UnsupportedOperationException("TODO: read a line, write it back, repeat until EOF");
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
