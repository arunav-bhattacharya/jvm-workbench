package workbench.quotes.l01;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.util.concurrent.TimeUnit;

/** The quote server: Netty 4.2, NIO transport, 127.0.0.1 and a free port. */
public final class QuoteServer implements AutoCloseable {
    private final EventLoopGroup group;
    private final Channel serverChannel;

    public QuoteServer(int loops, QuoteSource source) throws InterruptedException {
        group = new MultiThreadIoEventLoopGroup(loops, NioIoHandler.newFactory());
        serverChannel = new ServerBootstrap()
                .group(group)                                           // the same loops accept and serve
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ch.pipeline().addLast(QuotePipeline.handlers(source));
                    }
                })
                .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();
    }

    public int port() {
        return ((InetSocketAddress) serverChannel.localAddress()).getPort();
    }

    public EventLoopGroup group() {
        return group;
    }

    /** Close the listening socket: no new connections. Open connections keep working. */
    public void stopAccepting() {
        serverChannel.close().syncUninterruptibly();
    }

    @Override
    public void close() {
        stopAccepting();                                                // 1. no new connections
        group.shutdownGracefully(0, 2, TimeUnit.SECONDS)                // 2. closes every open channel,
                .syncUninterruptibly();                                 //    then stops the loop threads
    }
}
