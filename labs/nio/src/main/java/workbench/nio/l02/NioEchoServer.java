package workbench.nio.l02;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardSocketOptions;
import java.nio.ByteBuffer;
import java.nio.channels.ClosedSelectorException;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.Iterator;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A single-threaded echo server on a {@link Selector}: one thread serves every connection.
 *
 * <p>It works in a quick manual test, but it has two bugs that show up under load:
 * <ol>
 *   <li>It loses data. A non-blocking {@code write} may send only part of the buffer, and
 *       {@code serve} throws the unsent rest away. It also closes the connection on EOF even
 *       when it still holds bytes the client hasn't received.</li>
 *   <li>It busy-spins. Every connection is registered for {@code OP_WRITE} forever, and a socket
 *       with free send-buffer space is always writable, so {@code select()} never sleeps.</li>
 * </ol>
 * Fix {@link #accept} and {@link #serve} so the server echoes every byte, closes only after the
 * last byte is written, and is registered for {@code OP_WRITE} only while it has pending bytes.
 * Bonus: stop reading ({@code OP_READ} off) while the buffer is full.
 */
public final class NioEchoServer implements AutoCloseable {
    /** Per-connection state, kept as the key's attachment. */
    static final class Conn {
        final ByteBuffer buf = ByteBuffer.allocateDirect(16 * 1024);   // write mode between calls
        boolean eof;                                                    // the client half-closed
    }

    private final Selector selector;
    private final ServerSocketChannel server;
    private final AtomicLong wakeups = new AtomicLong();

    public NioEchoServer() throws IOException {
        selector = Selector.open();
        server = ServerSocketChannel.open();
        server.bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0));
        server.configureBlocking(false);
        server.register(selector, SelectionKey.OP_ACCEPT);
        Thread loop = new Thread(this::runLoop, "nio-echo-loop");
        loop.setDaemon(true);
        loop.start();
    }

    public int port() throws IOException {
        return ((InetSocketAddress) server.getLocalAddress()).getPort();
    }

    /** How many times {@code select()} returned with at least one ready key. */
    public long wakeups() {
        return wakeups.get();
    }

    private void runLoop() {
        try {
            while (selector.isOpen()) {
                if (selector.select() > 0) wakeups.incrementAndGet();
                Iterator<SelectionKey> it = selector.selectedKeys().iterator();
                while (it.hasNext()) {
                    SelectionKey key = it.next();
                    it.remove();                                   // the selector never removes keys for you
                    if (!key.isValid()) continue;
                    try {
                        if (key.isAcceptable()) accept();
                        else serve(key);
                    } catch (IOException e) {
                        key.cancel();
                        key.channel().close();
                    }
                }
            }
        } catch (IOException | ClosedSelectorException e) {
            // closed
        }
    }

    private void accept() throws IOException {
        SocketChannel ch = server.accept();
        if (ch == null) return;
        ch.configureBlocking(false);
        ch.setOption(StandardSocketOptions.SO_SNDBUF, 8 * 1024);   // small on purpose: partial writes come early
        ch.register(selector, SelectionKey.OP_READ | SelectionKey.OP_WRITE, new Conn());   // BUG: OP_WRITE forever
    }

    private void serve(SelectionKey key) throws IOException {
        SocketChannel ch = (SocketChannel) key.channel();
        Conn conn = (Conn) key.attachment();
        if (key.isReadable()) {
            if (ch.read(conn.buf) < 0) conn.eof = true;
        }
        conn.buf.flip();
        ch.write(conn.buf);        // BUG: may write only some of the bytes...
        conn.buf.clear();          // ...and clear() forgets the rest
        if (conn.eof) ch.close();  // BUG: closes even if bytes are still waiting to be sent
    }

    @Override
    public void close() throws IOException {
        selector.close();
        server.close();
    }
}
