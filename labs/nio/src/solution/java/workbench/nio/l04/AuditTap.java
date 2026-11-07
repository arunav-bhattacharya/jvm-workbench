package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;

import java.util.concurrent.atomic.AtomicLong;

public class AuditTap extends ChannelInboundHandlerAdapter {
    private final AtomicLong bytesSeen = new AtomicLong();

    public long bytesSeen() {
        return bytesSeen.get();
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        bytesSeen.addAndGet(((ByteBuf) msg).readableBytes());
        ctx.fireChannelRead(msg);   // pass the same buffer on: ownership moves to the next handler, no copy
    }
}
