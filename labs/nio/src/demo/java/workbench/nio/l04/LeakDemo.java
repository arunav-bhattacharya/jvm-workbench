package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufAllocator;
import io.netty.buffer.ByteBufUtil;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.util.ResourceLeakDetector;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/** A handler drops every message without releasing it. PARANOID leak detection reports it. */
public class LeakDemo {
    public static void main(String[] args) throws Exception {
        ResourceLeakDetector.setLevel(ResourceLeakDetector.Level.PARANOID);   // track every buffer
        List<String> leaks = new CopyOnWriteArrayList<>();
        ByteBufUtil.setLeakListener((type, records) -> leaks.add(type));

        EmbeddedChannel ch = new EmbeddedChannel(new ChannelInboundHandlerAdapter() {
            @Override
            public void channelRead(ChannelHandlerContext ctx, Object msg) {
                // BUG: neither released nor passed on with ctx.fireChannelRead(msg)
            }
        });
        for (int i = 0; i < 10; i++) {
            ByteBuf m = ByteBufAllocator.DEFAULT.buffer(32);
            m.writeInt(i);
            ch.writeInbound(m);
        }
        ch.finishAndReleaseAll();

        // a leak is noticed when the buffer object is garbage-collected while refCnt > 0,
        // and reported on a later allocation
        for (int i = 0; i < 40 && leaks.isEmpty(); i++) {
            System.gc();
            Thread.sleep(20);
            ByteBufAllocator.DEFAULT.buffer(8).release();
        }
        Thread.sleep(100);
        System.out.println("10 buffers leaked; the listener saw " + leaks.size() + " report(s): " + leaks);
    }
}
