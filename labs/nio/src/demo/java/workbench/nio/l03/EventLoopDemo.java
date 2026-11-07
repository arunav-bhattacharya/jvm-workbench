package workbench.nio.l03;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;

import java.io.InputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.concurrent.TimeUnit;

/** Which event-loop thread serves each connection? One acceptor loop, two worker loops, four clients. */
public class EventLoopDemo {
    public static void main(String[] args) throws Exception {
        MultiThreadIoEventLoopGroup defaults = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
        System.out.println("default loop count: " + defaults.executorCount()
                + " (availableProcessors=" + Runtime.getRuntime().availableProcessors() + ")");
        defaults.shutdownGracefully(0, 0, TimeUnit.SECONDS).sync();

        EventLoopGroup boss = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());     // accepts
        EventLoopGroup workers = new MultiThreadIoEventLoopGroup(2, NioIoHandler.newFactory());  // serves
        try {
            Channel server = new ServerBootstrap()
                    .group(boss, workers)
                    .channel(NioServerSocketChannel.class)
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) {
                            ch.pipeline().addLast(new ChannelInboundHandlerAdapter() {
                                @Override
                                public void channelActive(ChannelHandlerContext ctx) {
                                    System.out.printf("client port %d registered on %s, inEventLoop=%s%n",
                                            ((InetSocketAddress) ctx.channel().remoteAddress()).getPort(),
                                            Thread.currentThread().getName(), ctx.channel().eventLoop().inEventLoop());
                                }

                                @Override
                                public void channelRead(ChannelHandlerContext ctx, Object msg) {
                                    System.out.printf("   bytes from port %d handled on %s%n",
                                            ((InetSocketAddress) ctx.channel().remoteAddress()).getPort(),
                                            Thread.currentThread().getName());
                                    ctx.writeAndFlush(msg);   // echo: the write takes ownership of msg, no release here
                                }
                            });
                        }
                    })
                    .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();
            int port = ((InetSocketAddress) server.localAddress()).getPort();

            for (int i = 0; i < 4; i++) {
                try (Socket client = new Socket(InetAddress.getLoopbackAddress(), port)) {
                    client.getOutputStream().write("hi".getBytes());
                    InputStream in = client.getInputStream();
                    in.readNBytes(2);
                }
            }
            server.close().sync();
        } finally {
            boss.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync();
            workers.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync();
        }
    }
}
