package workbench.quotes.l01;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.handler.codec.LineBasedFrameDecoder;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import static java.nio.charset.StandardCharsets.UTF_8;

/** Feeds a line pipeline by hand: framing, request ids, replies out of order, and a line that is too long. */
public class ProtocolDemo {
    static final Map<String, CompletableFuture<String>> pending = new HashMap<>();

    // each request waits for a price that main() supplies by hand
    static class PendingHandler extends SimpleChannelInboundHandler<String> {
        @Override
        protected void channelRead0(ChannelHandlerContext ctx, String line) {
            String[] p = line.split(" ");
            CompletableFuture<String> price = new CompletableFuture<>();
            pending.put(p[1], price);
            price.whenCompleteAsync((v, e) -> ctx.writeAndFlush(p[0] + " OK " + p[1] + " " + v + "\n"), ctx.executor());
        }

        @Override
        public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
            ctx.writeAndFlush("ERR line too long\n").addListener(ChannelFutureListener.CLOSE);
        }
    }

    public static void main(String[] args) {
        int maxLine = args.length > 0 ? Integer.parseInt(args[0]) : 64;
        EmbeddedChannel ch = new EmbeddedChannel(
                new LineBasedFrameDecoder(maxLine), new StringDecoder(UTF_8), new StringEncoder(UTF_8), new PendingHandler());
        step(ch, "in \"7 EUR\"", () -> ch.writeInbound(buf("7 EUR")));
        step(ch, "in \"USD\\n8 GBPUSD\\n\"", () -> ch.writeInbound(buf("USD\n8 GBPUSD\n")));
        step(ch, "GBPUSD answers first", () -> answer("GBPUSD", "1.2710 fjord"));
        step(ch, "EURUSD answers", () -> answer("EURUSD", "1.0842 northbank"));
        step(ch, "in a 100-byte line", () -> ch.writeInbound(buf("x".repeat(100) + "\n")));
        System.out.println("channel open: " + ch.isOpen());
    }

    static void answer(String symbol, String price) {
        CompletableFuture<String> f = pending.get(symbol);
        if (f != null) f.complete(price);
    }

    static ByteBuf buf(String s) {
        return Unpooled.copiedBuffer(s, UTF_8);
    }

    static void step(EmbeddedChannel ch, String what, Runnable action) {
        if (ch.isOpen()) action.run();
        ch.runPendingTasks();                        // run the callbacks queued on the channel's loop
        List<String> out = new ArrayList<>();
        for (ByteBuf b; (b = ch.readOutbound()) != null; b.release()) out.add(b.toString(UTF_8).trim());
        System.out.printf("%-24s -> out %s%n", what, out.isEmpty() ? "(nothing)" : out);
    }
}
