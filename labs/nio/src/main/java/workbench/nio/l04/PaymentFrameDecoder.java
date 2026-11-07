package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.ByteToMessageDecoder;

import java.util.List;

/**
 * Turns ONE frame body into a {@link PaymentMessage}. It runs after
 * {@code LengthFieldBasedFrameDecoder}, which has already cut the stream into whole frames and
 * stripped the 4-byte length, so {@code in} holds exactly {@code [byte type][UTF-8 body]}.
 *
 * <p>Read the type byte, then the rest as UTF-8, and add one message to {@code out}. Read the body
 * without allocating a new buffer: {@code readBytes(int)} returns a buffer you would have to release.
 */
public class PaymentFrameDecoder extends ByteToMessageDecoder {
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) {
        throw new UnsupportedOperationException("TODO: read the type byte and the UTF-8 body");
    }
}
