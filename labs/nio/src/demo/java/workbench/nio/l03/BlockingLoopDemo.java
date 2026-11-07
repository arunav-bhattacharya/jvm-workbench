package workbench.nio.l03;

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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static java.nio.charset.StandardCharsets.UTF_8;

/** One event loop. Client A asks for SLOW (a 1 s "JDBC call"); client B asks for FAST 50 ms later. */
public class BlockingLoopDemo {
    public static void main(String[] args) throws Exception {
        run(false);
        run(true);
    }

    static String work(String line) throws InterruptedException {
        if (line.equals("SLOW")) Thread.sleep(1_000);   // stands in for a blocking JDBC call
        return line + " on " + Thread.currentThread().getName();
    }

    static void run(boolean dispatch) throws Exception {
        EventLoopGroup group = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());
        ExecutorService blockingPool = Executors.newFixedThreadPool(4, r -> new Thread(r, "app-blocking-pool"));
        try {
            Channel server = new ServerBootstrap().group(group).channel(NioServerSocketChannel.class)
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) {
                            ch.pipeline().addLast(new LineBasedFrameDecoder(1024), new StringDecoder(UTF_8), new StringEncoder(UTF_8),
                                    new SimpleChannelInboundHandler<String>() {
                                        @Override
                                        protected void channelRead0(ChannelHandlerContext ctx, String line) throws Exception {
                                            if (!dispatch) {
                                                ctx.writeAndFlush(work(line) + "\n");          // blocks the event loop
                                                return;
                                            }
                                            blockingPool.execute(() -> {                         // leave the loop for the slow part
                                                String reply;
                                                try { reply = work(line); } catch (InterruptedException e) { reply = "interrupted"; }
                                                ctx.writeAndFlush(reply + "\n");                 // safe from any thread
                                            });
                                        }
                                    });
                        }
                    })
                    .bind(InetAddress.getLoopbackAddress(), 0).sync().channel();
            int port = ((InetSocketAddress) server.localAddress()).getPort();
            try (Socket a = new Socket(InetAddress.getLoopbackAddress(), port);
                 Socket b = new Socket(InetAddress.getLoopbackAddress(), port)) {
                BufferedReader aIn = new BufferedReader(new InputStreamReader(a.getInputStream(), UTF_8));
                BufferedReader bIn = new BufferedReader(new InputStreamReader(b.getInputStream(), UTF_8));
                a.getOutputStream().write("SLOW\n".getBytes(UTF_8));
                Thread.sleep(50);

                long t0 = System.nanoTime();
                b.getOutputStream().write("FAST\n".getBytes(UTF_8));
                // lag probe: how long until a trivial task runs on the loop?
                long lagMs = group.next().submit(() -> (System.nanoTime() - t0) / 1_000_000).get(5, TimeUnit.SECONDS);
                String fast = bIn.readLine();
                long fastMs = (System.nanoTime() - t0) / 1_000_000;

                System.out.println(dispatch ? "[dispatch to app pool]" : "[blocking in the handler]");
                System.out.printf("   event-loop lag probe: %d ms%n", lagMs);
                System.out.printf("   FAST reply after %d ms: %s%n", fastMs, fast);
                System.out.printf("   SLOW reply: %s%n", aIn.readLine());
            }
            server.close().sync();
        } finally {
            group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync();   // close channels and loops first...
            blockingPool.shutdown();                                     // ...then the pool they write from
        }
    }
}
