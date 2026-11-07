package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Sits first in the pipeline and counts the raw bytes that arrive, for the audit dashboard.
 * Then it passes every buffer on, unchanged, to the next handler.
 *
 * <p>It leaks: under load the service's direct memory grows until it fails. Find the leak and fix
 * it. Remember the rule: whoever touches a reference-counted message last must release it.
 */
public class AuditTap extends ChannelInboundHandlerAdapter {
    private final AtomicLong bytesSeen = new AtomicLong();

    public long bytesSeen() {
        return bytesSeen.get();
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        ByteBuf in = (ByteBuf) msg;
        bytesSeen.addAndGet(in.readableBytes());
        ctx.fireChannelRead(in.copy());   // passes a copy on... and nobody ever releases the original
    }
}
