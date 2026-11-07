package workbench.nio.l03;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.ChannelOutboundHandlerAdapter;
import io.netty.channel.ChannelPromise;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.handler.codec.LineBasedFrameDecoder;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;

import java.util.List;

import static java.nio.charset.StandardCharsets.UTF_8;

/** Feeds bytes into a pipeline in fragments and prints what each stage sees, inbound and outbound. */
public class PipelineDemo {
    static String describe(Object msg) {
        String text = msg instanceof ByteBuf b ? b.toString(UTF_8) : msg.toString();
        String type = msg instanceof ByteBuf ? "ByteBuf" : msg.getClass().getSimpleName();
        return type + " \"" + text.replace("\n", "\\n") + "\"";
    }

    public static void main(String[] args) {
        EmbeddedChannel ch = new EmbeddedChannel(
                new LineBasedFrameDecoder(64),                       // inbound: bytes -> one ByteBuf per line
                new ChannelInboundHandlerAdapter() {                 // inbound tap
                    @Override public void channelRead(ChannelHandlerContext ctx, Object msg) {
                        System.out.println("   in,  after framing : " + describe(msg));
                        ctx.fireChannelRead(msg);                    // pass it on (ownership moves with it)
                    }
                },
                new StringDecoder(UTF_8),                            // inbound: ByteBuf -> String
                new ChannelOutboundHandlerAdapter() {                // outbound tap, nearer the head than the encoder
                    @Override public void write(ChannelHandlerContext ctx, Object msg, ChannelPromise promise) {
                        System.out.println("   out, to the wire   : " + describe(msg));
                        ctx.write(msg, promise);
                    }
                },
                new StringEncoder(UTF_8),                            // outbound: String -> ByteBuf
                new SimpleChannelInboundHandler<String>() {          // business logic, last
                    @Override protected void channelRead0(ChannelHandlerContext ctx, String line) {
                        System.out.println("   in,  business sees : String \"" + line + "\"");
                        ctx.writeAndFlush(line.toUpperCase() + "\n");   // travels toward the head
                    }
                });

        for (String fragment : List.of("hel", "lo\nwor", "ld\n")) {
            System.out.println("writeInbound(\"" + fragment.replace("\n", "\\n") + "\")");
            ch.writeInbound(Unpooled.copiedBuffer(fragment, UTF_8));
            ByteBuf out;
            while ((out = ch.readOutbound()) != null) out.release();
        }
        try {
            ch.writeInbound(Unpooled.copiedBuffer("x".repeat(100) + "\n", UTF_8));
        } catch (Exception e) {
            System.out.println("100-byte line -> " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        System.out.println("finish() = " + ch.finish());
    }
}
