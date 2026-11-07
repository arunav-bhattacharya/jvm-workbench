package workbench.nio.l08;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.DefaultFileRegion;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.IoHandlerFactory;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.ServerChannel;
import io.netty.channel.epoll.Epoll;
import io.netty.channel.epoll.EpollIoHandler;
import io.netty.channel.epoll.EpollServerSocketChannel;
import io.netty.channel.kqueue.KQueue;
import io.netty.channel.kqueue.KQueueIoHandler;
import io.netty.channel.kqueue.KQueueServerSocketChannel;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.channel.uring.IoUring;
import io.netty.channel.uring.IoUringIoHandler;
import io.netty.channel.uring.IoUringServerSocketChannel;

import java.io.InputStream;
import java.io.RandomAccessFile;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Sends a 32 MiB file with Netty's DefaultFileRegion over every transport available on this machine. */
public class TransportsDemo {
    public static void main(String[] args) throws Exception {
        long size = 32L << 20;
        Path file = Files.createTempFile("statement", ".bin");
        try (RandomAccessFile raf = new RandomAccessFile(file.toFile(), "rw")) {
            raf.setLength(size);
        }
        try {
            send("nio", NioIoHandler.newFactory(), NioServerSocketChannel.class, file, size);
            if (Epoll.isAvailable()) send("epoll", EpollIoHandler.newFactory(), EpollServerSocketChannel.class, file, size);
            else System.out.println("epoll    unavailable: " + Epoll.unavailabilityCause());
            if (KQueue.isAvailable()) send("kqueue", KQueueIoHandler.newFactory(), KQueueServerSocketChannel.class, file, size);
            else System.out.println("kqueue   unavailable: " + KQueue.unavailabilityCause());
            if (IoUring.isAvailable()) send("io_uring", IoUringIoHandler.newFactory(), IoUringServerSocketChannel.class, file, size);
            else System.out.println("io_uring unavailable: " + IoUring.unavailabilityCause());
        } finally {
            Files.delete(file);
        }
    }

    static void send(String name, IoHandlerFactory factory, Class<? extends ServerChannel> channelClass, Path file, long size) throws Exception {
        EventLoopGroup group = new MultiThreadIoEventLoopGroup(1, factory);   // same group type, different IoHandler
        try {
            Channel server = new ServerBootstrap().group(group).channel(channelClass)
                    .childHandler(new ChannelInboundHandlerAdapter() {
                        @Override
                        public void channelActive(ChannelHandlerContext ctx) {
                            ctx.writeAndFlush(new DefaultFileRegion(file.toFile(), 0, size))   // zero-copy where the transport can
                                    .addListener(ChannelFutureListener.CLOSE);
                        }
                    })
                    .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();
            long t0 = System.nanoTime(), received = 0;
            try (Socket s = new Socket(InetAddress.getLoopbackAddress(), ((InetSocketAddress) server.localAddress()).getPort())) {
                InputStream in = s.getInputStream();
                byte[] buf = new byte[1 << 16];
                int r;
                while ((r = in.read(buf)) >= 0) received += r;
            }
            System.out.printf("%-8s received %,d bytes in %d ms%n", name, received, (System.nanoTime() - t0) / 1_000_000);
            server.close().sync();
        } finally {
            group.shutdownGracefully(0, 0, TimeUnit.SECONDS).sync();
        }
    }
}
