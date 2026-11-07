package workbench.nio.l04;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.Socket;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * An echo server and a client that writes 8 MiB fast but reads slowly. How much piles up in the
 * server's outbound buffer, with and without backpressure?
 */
public class BackpressureDemo {
    public static void main(String[] args) throws Exception {
        for (boolean backpressure : new boolean[] {false, true}) {
            System.out.printf("backpressure=%-5s -> peak bytes waiting in the outbound buffer: %,d%n",
                    backpressure, peakPending(backpressure, 8));
        }
    }

    static long peakPending(boolean backpressure, int megabytes) throws Exception {
        EventLoopGroup group = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());
        AtomicLong peak = new AtomicLong();
        try {
            Channel server = new ServerBootstrap().group(group).channel(NioServerSocketChannel.class)
                    .childOption(ChannelOption.SO_SNDBUF, 32 * 1024)
                    .childOption(ChannelOption.SO_RCVBUF, 32 * 1024)
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) {
                            ch.pipeline().addLast(new ChannelInboundHandlerAdapter() {
                                @Override
                                public void channelRead(ChannelHandlerContext ctx, Object msg) {
                                    ctx.write(msg);   // queue the echo in the outbound buffer
                                    long pending = ctx.channel().unsafe().outboundBuffer().totalPendingWriteBytes();
                                    peak.accumulateAndGet(pending, Math::max);
                                }

                                @Override
                                public void channelReadComplete(ChannelHandlerContext ctx) {
                                    ctx.flush();
                                    if (backpressure && !ctx.channel().isWritable()) {
                                        ctx.channel().config().setAutoRead(false);   // stop reading from a peer we can't write to
                                    }
                                }

                                @Override
                                public void channelWritabilityChanged(ChannelHandlerContext ctx) {
                                    if (backpressure && ctx.channel().isWritable()) {
                                        ctx.channel().config().setAutoRead(true);    // drained below the low water mark
                                    }
                                    ctx.fireChannelWritabilityChanged();
                                }
                            });
                        }
                    })
                    .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();

            int total = megabytes << 20;
            try (Socket s = new Socket()) {
                s.setReceiveBufferSize(32 * 1024);
                s.setSendBufferSize(32 * 1024);
                s.connect(server.localAddress());
                Thread writer = new Thread(() -> {                 // the fast writer
                    try {
                        OutputStream out = s.getOutputStream();
                        byte[] chunk = new byte[64 * 1024];
                        for (int i = 0; i < total / chunk.length; i++) out.write(chunk);
                        s.shutdownOutput();
                    } catch (IOException ignored) { }
                });
                writer.start();
                InputStream in = s.getInputStream();               // the slow reader: 20 ms pause per 128 KiB
                byte[] buf = new byte[16 * 1024];
                long got = 0;
                int n;
                while (got < total && (n = in.read(buf)) >= 0) {
                    got += n;
                    if ((got & ((128 << 10) - 1)) < n) Thread.sleep(20);
                }
                writer.join();
            }
            server.close().sync();
        } finally {
            group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync();
        }
        return peak.get();
    }
}
