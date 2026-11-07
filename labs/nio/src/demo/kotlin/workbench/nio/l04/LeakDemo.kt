package workbench.nio.l04

import io.netty.buffer.ByteBufAllocator
import io.netty.buffer.ByteBufUtil
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInboundHandlerAdapter
import io.netty.channel.embedded.EmbeddedChannel
import io.netty.util.ResourceLeakDetector
import java.util.concurrent.CopyOnWriteArrayList

/** A handler drops every message without releasing it. PARANOID leak detection reports it. */
fun main() {
    ResourceLeakDetector.setLevel(ResourceLeakDetector.Level.PARANOID)   // track every buffer
    val leaks = CopyOnWriteArrayList<String>()
    ByteBufUtil.setLeakListener { type, _ -> leaks += type }

    val ch = EmbeddedChannel(object : ChannelInboundHandlerAdapter() {
        override fun channelRead(ctx: ChannelHandlerContext, msg: Any) {
            // BUG: neither released nor passed on with ctx.fireChannelRead(msg)
        }
    })
    repeat(10) { i ->
        val m = ByteBufAllocator.DEFAULT.buffer(32)
        m.writeInt(i)
        ch.writeInbound(m)
    }
    ch.finishAndReleaseAll()

    // a leak is noticed when the buffer object is garbage-collected while refCnt > 0,
    // and reported on a later allocation
    var i = 0
    while (i++ < 40 && leaks.isEmpty()) {
        System.gc()
        Thread.sleep(20)
        ByteBufAllocator.DEFAULT.buffer(8).release()
    }
    Thread.sleep(100)
    println("10 buffers leaked; the listener saw ${leaks.size} report(s): $leaks")
}
