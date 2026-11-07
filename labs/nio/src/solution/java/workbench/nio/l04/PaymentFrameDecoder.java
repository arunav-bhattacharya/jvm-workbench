package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.ByteToMessageDecoder;

import java.util.List;

import static java.nio.charset.StandardCharsets.UTF_8;

public class PaymentFrameDecoder extends ByteToMessageDecoder {
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) {
        int type = in.readByte();
        // readCharSequence decodes in place: no new ByteBuf to release (readBytes(n) would allocate one)
        String body = in.readCharSequence(in.readableBytes(), UTF_8).toString();
        out.add(new PaymentMessage(type, body));
    }
}
