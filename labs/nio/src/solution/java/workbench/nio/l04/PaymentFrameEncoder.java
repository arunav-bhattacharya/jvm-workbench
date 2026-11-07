package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.MessageToByteEncoder;

import static java.nio.charset.StandardCharsets.UTF_8;

public class PaymentFrameEncoder extends MessageToByteEncoder<PaymentMessage> {
    @Override
    protected void encode(ChannelHandlerContext ctx, PaymentMessage msg, ByteBuf out) {
        byte[] body = msg.body().getBytes(UTF_8);
        out.writeInt(1 + body.length);   // the length counts the type byte and the body
        out.writeByte(msg.type());
        out.writeBytes(body);            // Netty releases `out` after the write; we allocated nothing else
    }
}
