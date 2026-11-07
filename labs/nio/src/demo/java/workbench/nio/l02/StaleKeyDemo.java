package workbench.nio.l02;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.Iterator;

/** One message arrives. How many times does the loop think the channel is readable? */
public class StaleKeyDemo {
    public static void main(String[] args) throws Exception {
        run(true);
        run(false);
    }

    static void run(boolean removeHandledKeys) throws Exception {
        try (Selector selector = Selector.open();
             ServerSocketChannel server = ServerSocketChannel.open()) {
            server.bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0));
            try (SocketChannel client = SocketChannel.open(server.getLocalAddress());
                 SocketChannel conn = server.accept()) {
                conn.configureBlocking(false);
                conn.register(selector, SelectionKey.OP_READ);
                client.write(ByteBuffer.wrap("auth-1".getBytes()));   // exactly one message

                ByteBuffer buf = ByteBuffer.allocate(64);
                int loops = 0, handled = 0, bytes = 0;
                long end = System.nanoTime() + 300_000_000L;
                while (System.nanoTime() < end) {
                    selector.select(50);
                    loops++;
                    Iterator<SelectionKey> it = selector.selectedKeys().iterator();
                    while (it.hasNext()) {
                        SelectionKey key = it.next();
                        if (removeHandledKeys) it.remove();
                        if (key.isReadable()) {                   // ready set from the last select that added the key
                            handled++;
                            buf.clear();
                            bytes += Math.max(0, conn.read(buf));
                        }
                    }
                }
                System.out.printf("remove handled keys=%-5s loops=%d, handled as readable %d times, bytes read %d%n",
                        removeHandledKeys, loops, handled, bytes);
            }
        }
    }
}
