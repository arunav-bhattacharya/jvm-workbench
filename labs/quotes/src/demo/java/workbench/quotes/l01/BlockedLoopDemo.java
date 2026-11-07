package workbench.quotes.l01;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.LineBasedFrameDecoder;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static java.nio.charset.StandardCharsets.UTF_8;

/** One event loop, ten clients, a provider that answers after 100 ms: join() on the loop vs handing the future back. */
public class BlockedLoopDemo {
    static final ScheduledExecutorService provider = Executors.newSingleThreadScheduledExecutor();
    static final AtomicInteger inFlight = new AtomicInteger();
    static final AtomicInteger peak = new AtomicInteger();

    static CompletableFuture<String> quote(String symbol) {
        peak.accumulateAndGet(inFlight.incrementAndGet(), Math::max);       // count quotes waiting at once
        CompletableFuture<String> f = new CompletableFuture<>();
        provider.schedule(() -> {
            inFlight.decrementAndGet();
            f.complete(symbol + " 1.0842");
        }, 100, TimeUnit.MILLISECONDS);
        return f;
    }

    static final class QuoteOnLoop extends SimpleChannelInboundHandler<String> {
        private final boolean block;

        QuoteOnLoop(boolean block) {
            this.block = block;
        }

        @Override
        protected void channelRead0(ChannelHandlerContext ctx, String line) {
            String[] p = line.split(" ");
            CompletableFuture<String> q = quote(p[1]);
            if (block) {
                ctx.writeAndFlush(p[0] + " OK " + q.join() + "\n");                // waits 100 ms on the loop
            } else {
                q.whenCompleteAsync((v, e) -> ctx.writeAndFlush(p[0] + " OK " + v + "\n"), ctx.executor());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        run(true);
        run(false);
        provider.shutdown();
    }

    static void run(boolean block) throws Exception {
        EventLoopGroup group = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());
        try {
            Channel server = new ServerBootstrap().group(group).channel(NioServerSocketChannel.class)
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) {
                            ch.pipeline().addLast(new LineBasedFrameDecoder(64), new StringDecoder(UTF_8),
                                    new StringEncoder(UTF_8), new QuoteOnLoop(block));
                        }
                    })
                    .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();
            int port = ((InetSocketAddress) server.localAddress()).getPort();
            List<Socket> clients = new ArrayList<>();
            for (int i = 0; i < 10; i++) clients.add(new Socket(InetAddress.getLoopbackAddress(), port));

            peak.set(0);
            long t0 = System.nanoTime();
            for (int i = 0; i < 10; i++) clients.get(i).getOutputStream().write((i + " EURUSD\n").getBytes(UTF_8));
            for (Socket c : clients) new BufferedReader(new InputStreamReader(c.getInputStream(), UTF_8)).readLine();
            long ms = (System.nanoTime() - t0) / 1_000_000;
            System.out.printf("%-6s 10 replies after %,5d ms; quotes waiting at the same time: %2d%n",
                    block ? "join" : "async", ms, peak.get());
            for (Socket c : clients) c.close();
        } finally {
            group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync();
        }
    }
}
