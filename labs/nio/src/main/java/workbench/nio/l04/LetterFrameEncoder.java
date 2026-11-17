package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.MessageToByteEncoder;

/** Writes a {@link Letter} as {@code [int length][byte type][UTF-8 body]}. */
public class LetterFrameEncoder extends MessageToByteEncoder<Letter> {
    @Override
    protected void encode(ChannelHandlerContext ctx, Letter msg, ByteBuf out) {
        throw new UnsupportedOperationException("TODO: write the length (1 + body bytes), the type byte, then the body");
    }
}
