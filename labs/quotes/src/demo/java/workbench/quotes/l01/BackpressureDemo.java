package workbench.quotes.l01;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.LineBasedFrameDecoder;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;
import io.netty.handler.flow.FlowControlHandler;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import static java.nio.charset.StandardCharsets.UTF_8;

/** A client pipelines 20,000 requests and reads nothing for 500 ms. How much does the server take on? */
public class BackpressureDemo {
    static final int REQUESTS = 20_000;
    static final int MAX_IN_FLIGHT = 16;

    enum Mode { NONE, AUTO_READ, AUTO_READ_AND_FLOW_CONTROL }

    static final AtomicInteger taken = new AtomicInteger();
    static final AtomicLong peakPending = new AtomicLong();

    static final class Answer extends SimpleChannelInboundHandler<String> {
        private final boolean policy;
        private int inFlight;                                   // only the loop touches it

        Answer(boolean policy) {
            this.policy = policy;
        }

        @Override
        protected void channelRead0(ChannelHandlerContext ctx, String line) {
            taken.incrementAndGet();
            inFlight++;
            update(ctx);
            CompletableFuture.completedFuture(line.split(" ")[0]).whenCompleteAsync((id, e) -> {
                inFlight--;
                ctx.writeAndFlush(id + " OK EURUSD 1.0842 northbank\n");
                peakPending.accumulateAndGet(ctx.channel().unsafe().outboundBuffer().totalPendingWriteBytes(), Math::max);
                update(ctx);
            }, ctx.executor());
        }

        @Override
        public void channelWritabilityChanged(ChannelHandlerContext ctx) {
            update(ctx);
            ctx.fireChannelWritabilityChanged();
        }

        private void update(ChannelHandlerContext ctx) {
            if (policy) ctx.channel().config().setAutoRead(ctx.channel().isWritable() && inFlight < MAX_IN_FLIGHT);
        }
    }

    public static void main(String[] args) throws Exception {
        for (Mode m : Mode.values()) run(m);
    }

    static void run(Mode mode) throws Exception {
        taken.set(0);
        peakPending.set(0);
        EventLoopGroup group = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());
        try {
            Channel server = new ServerBootstrap().group(group).channel(NioServerSocketChannel.class)
                    .childOption(ChannelOption.SO_SNDBUF, 8 * 1024)
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) {
                            ch.pipeline().addLast(new LineBasedFrameDecoder(64), new StringDecoder(UTF_8), new StringEncoder(UTF_8));
                            if (mode == Mode.AUTO_READ_AND_FLOW_CONTROL) ch.pipeline().addLast(new FlowControlHandler());
                            ch.pipeline().addLast(new Answer(mode != Mode.NONE));
                        }
                    })
                    .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();
            int port = ((InetSocketAddress) server.localAddress()).getPort();

            try (Socket client = new Socket()) {
                client.setReceiveBufferSize(8 * 1024);              // a slow client with a small window
                client.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), port));
                Thread writer = Thread.ofPlatform().start(() -> {
                    try {
                        OutputStream out = new BufferedOutputStream(client.getOutputStream());
                        for (int i = 0; i < REQUESTS; i++) out.write((i + " EURUSD\n").getBytes(UTF_8));
                        out.flush();
                    } catch (Exception ignored) {
                    }
                });
                Thread.sleep(500);                                  // the client reads nothing for 500 ms
                int takenWhileIdle = taken.get();
                BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream(), UTF_8));
                int replies = 0;
                while (replies < REQUESTS && in.readLine() != null) replies++;
                writer.join();
                System.out.printf("%-27s taken while the client read nothing: %,6d   peak outbound: %,9d bytes   replies: %,d%n",
                        mode, takenWhileIdle, peakPending.get(), replies);
            }
        } finally {
            group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync();
        }
    }
}
