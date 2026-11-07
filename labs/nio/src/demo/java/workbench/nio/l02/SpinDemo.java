package workbench.nio.l02;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;

/** Counts how often select() wakes up on one idle connection, with and without OP_WRITE in the interest set. */
public class SpinDemo {
    public static void main(String[] args) throws Exception {
        try (Selector probe = Selector.open()) {
            System.out.println("Selector implementation: " + probe.getClass().getName());
        }
        System.out.println("idle 300 ms, interest OP_READ           : " + wakeups(SelectionKey.OP_READ) + " wakeups");
        System.out.println("idle 300 ms, interest OP_READ | OP_WRITE: "
                + wakeups(SelectionKey.OP_READ | SelectionKey.OP_WRITE) + " wakeups");
    }

    static long wakeups(int interest) throws Exception {
        try (Selector selector = Selector.open();
             ServerSocketChannel server = ServerSocketChannel.open()) {
            server.bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0));
            try (SocketChannel client = SocketChannel.open(server.getLocalAddress());
                 SocketChannel conn = server.accept()) {
                conn.configureBlocking(false);
                conn.register(selector, interest);
                long end = System.nanoTime() + 300_000_000L, count = 0;
                while (System.nanoTime() < end) {
                    if (selector.select(50) > 0) count++;   // nobody sends anything on this connection
                    selector.selectedKeys().clear();
                }
                return count;
            }
        }
    }
}
