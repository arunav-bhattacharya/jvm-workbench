package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufUtil;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.handler.codec.ByteToMessageDecoder;
import io.netty.handler.codec.LengthFieldBasedFrameDecoder;
import io.netty.handler.codec.MessageToByteEncoder;
import io.netty.handler.codec.TooLongFrameException;

import java.util.ArrayList;
import java.util.List;

import static java.nio.charset.StandardCharsets.UTF_8;

/** A length-prefixed codec fed in awkward slices: [int length][byte type][UTF-8 text]. */
public class CodecDemo {
    record Frame(int type, String text) { }

    static final class FrameEncoder extends MessageToByteEncoder<Frame> {
        @Override protected void encode(ChannelHandlerContext ctx, Frame f, ByteBuf out) {
            byte[] text = f.text().getBytes(UTF_8);
            out.writeInt(1 + text.length).writeByte(f.type()).writeBytes(text);
        }
    }

    static final class FrameDecoder extends ByteToMessageDecoder {   // runs after the length is stripped
        @Override protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) {
            int type = in.readByte();
            out.add(new Frame(type, in.readCharSequence(in.readableBytes(), UTF_8).toString()));
        }
    }

    static final class Approver extends SimpleChannelInboundHandler<Frame> {
        @Override protected void channelRead0(ChannelHandlerContext ctx, Frame f) {
            ctx.writeAndFlush(new Frame(f.type() + 1, f.text().toUpperCase()));
        }
    }

    static EmbeddedChannel server() {
        return new EmbeddedChannel(new LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4),
                new FrameDecoder(), new FrameEncoder(), new Approver());
    }

    public static void main(String[] args) {
        EmbeddedChannel encoder = new EmbeddedChannel(new FrameEncoder());
        encoder.writeOutbound(new Frame(1, "auth-1"), new Frame(7, "capture-1"));
        ByteBuf wire = Unpooled.buffer();
        ByteBuf part;
        while ((part = encoder.readOutbound()) != null) { wire.writeBytes(part); part.release(); }
        System.out.println("wire: " + wire.readableBytes() + " bytes, hex " + ByteBufUtil.hexDump(wire));

        EmbeddedChannel ch = server();
        int[] cuts = {3, 9, 14, wire.readableBytes()};   // inside the length, inside body 1, across the boundary, the rest
        int from = 0;
        for (int to : cuts) {
            ch.writeInbound(wire.retainedSlice(from, to - from));
            List<String> replies = new ArrayList<>();
            ByteBuf out;
            while ((out = ch.readOutbound()) != null) {
                replies.add("type=" + out.getByte(4) + " " + out.toString(5, out.readableBytes() - 5, UTF_8));
                out.release();
            }
            System.out.printf("bytes [%2d,%2d) -> replies %s%n", from, to, replies);
            from = to;
        }
        wire.release();
        try {
            ch.writeInbound(Unpooled.buffer().writeInt(5_000).writeByte(1));
        } catch (TooLongFrameException e) {
            System.out.println("length 5000 -> TooLongFrameException: " + e.getMessage());
        }
        System.out.println("finish() = " + ch.finish());
    }
}
