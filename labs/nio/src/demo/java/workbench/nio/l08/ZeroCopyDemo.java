package workbench.nio.l08;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.file.Files;
import java.nio.file.Path;

/** Sends a file over a loopback socket twice: FileChannel.transferTo (zero-copy) and read/write through a heap buffer. Arg: MiB (default 64). */
public class ZeroCopyDemo {
    public static void main(String[] args) throws Exception {
        long size = (args.length > 0 ? Long.parseLong(args[0]) : 64) << 20;
        Path file = Files.createTempFile("statement", ".bin");
        try (RandomAccessFile raf = new RandomAccessFile(file.toFile(), "rw")) {
            raf.setLength(size);
        }
        try {
            for (String mode : new String[] {"transferTo", "copy"}) send(file, size, mode);
        } finally {
            Files.delete(file);
        }
    }

    static void send(Path file, long size, String mode) throws Exception {
        try (ServerSocketChannel listener = ServerSocketChannel.open()
                .bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0))) {
            Thread receiver = new Thread(() -> {                     // drains the socket, counts bytes
                try (SocketChannel in = listener.accept()) {
                    ByteBuffer b = ByteBuffer.allocateDirect(1 << 20);
                    while (in.read(b) >= 0) b.clear();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            });
            receiver.start();
            long t0 = System.nanoTime();
            int calls = 0;
            try (FileChannel f = FileChannel.open(file); SocketChannel out = SocketChannel.open(listener.getLocalAddress())) {
                if (mode.equals("transferTo")) {
                    long sent = 0;
                    while (sent < size) {                            // may move less than asked: loop
                        sent += f.transferTo(sent, size - sent, out);
                        calls++;
                    }
                } else {
                    ByteBuffer b = ByteBuffer.allocate(64 * 1024);   // heap: the JDK copies it again, via a direct buffer
                    while (f.read(b) >= 0) {
                        b.flip();
                        while (b.hasRemaining()) out.write(b);
                        b.clear();
                        calls++;
                    }
                }
            }
            receiver.join();
            System.out.printf("%-10s %d MiB in %4d ms, %,d %s calls%n", mode, size >> 20,
                    (System.nanoTime() - t0) / 1_000_000, calls, mode.equals("copy") ? "read" : "transferTo");
        }
    }
}
