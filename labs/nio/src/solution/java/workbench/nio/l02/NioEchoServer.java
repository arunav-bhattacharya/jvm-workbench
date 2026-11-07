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

public final class NioEchoServer implements AutoCloseable {
    static final class Conn {
        final ByteBuffer buf = ByteBuffer.allocateDirect(16 * 1024);
        boolean eof;
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
                    it.remove();
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
        ch.register(selector, SelectionKey.OP_READ, new Conn());   // nothing to write yet
    }

    private void serve(SelectionKey key) throws IOException {
        SocketChannel ch = (SocketChannel) key.channel();
        Conn conn = (Conn) key.attachment();
        if (key.isReadable()) {
            if (ch.read(conn.buf) < 0) conn.eof = true;       // partial read: whatever the kernel had
        }
        conn.buf.flip();                                       // switch to reading what we hold
        if (conn.buf.hasRemaining()) ch.write(conn.buf);       // partial write: maybe only some of it
        conn.buf.compact();                                    // keep the unsent tail, back to write mode
        boolean pending = conn.buf.position() > 0;
        if (conn.eof && !pending) {                            // close only after the last byte went out
            ch.close();
            return;
        }
        int ops = 0;
        if (!conn.eof && conn.buf.hasRemaining()) ops |= SelectionKey.OP_READ;   // full buffer: stop reading
        if (pending) ops |= SelectionKey.OP_WRITE;                                // OP_WRITE only while bytes wait
        key.interestOps(ops);
    }

    @Override
    public void close() throws IOException {
        selector.close();
        server.close();
    }
}
