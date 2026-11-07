package workbench.quotes.scratch

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.*
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.SocketChannel
import io.netty.channel.socket.nio.NioServerSocketChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import io.netty.channel.embedded.EmbeddedChannel
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread
import kotlin.text.Charsets.UTF_8

val reads = AtomicInteger()
val pauses = AtomicInteger()
val paused = CountDownLatch(1)
val peak = AtomicLong()

class BP(val policy: Boolean) : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, msg: String) {
        reads.incrementAndGet()
        val id = msg.substringBefore(' ')
        ctx.writeAndFlush("$id OK EURUSD 1.08420 northbank\n")
        peak.accumulateAndGet(ctx.channel().unsafe().outboundBuffer()?.totalPendingWriteBytes() ?: 0, ::maxOf)
    }
    override fun channelWritabilityChanged(ctx: ChannelHandlerContext) {
        if (policy) {
            val w = ctx.channel().isWritable
            ctx.channel().config().isAutoRead = w
            if (!w) { pauses.incrementAndGet(); paused.countDown() }
        }
        ctx.fireChannelWritabilityChanged()
    }
}

fun main(args: Array<String>) {
    val policy = args.firstOrNull() != "off"
    // embedded writability check
    val ch = EmbeddedChannel(BP(true))
    ch.unsafe().outboundBuffer()!!.setUserDefinedWritability(1, false); ch.runPendingTasks()
    println("embedded: after false autoRead=${ch.config().isAutoRead}")
    ch.unsafe().outboundBuffer()!!.setUserDefinedWritability(1, true); ch.runPendingTasks()
    println("embedded: after true autoRead=${ch.config().isAutoRead}")

    val group = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
    val server = ServerBootstrap().group(group).channel(NioServerSocketChannel::class.java)
        .childOption(ChannelOption.SO_SNDBUF, 4096)
        .childOption(ChannelOption.WRITE_BUFFER_WATER_MARK, WriteBufferWaterMark(2048, 4096))
        .childHandler(object : ChannelInitializer<SocketChannel>() {
            override fun initChannel(c: SocketChannel) { c.pipeline().addLast(LineBasedFrameDecoder(64), StringDecoder(UTF_8), StringEncoder(UTF_8), BP(policy)) }
        }).bind(InetAddress.getLoopbackAddress(), 0).sync().channel()
    val port = (server.localAddress() as InetSocketAddress).port
    val n = 10_000
    val s = Socket()
    s.receiveBufferSize = 4096
    s.connect(InetSocketAddress(InetAddress.getLoopbackAddress(), port))
    s.soTimeout = 5000
    val writer = thread { val out = s.getOutputStream().buffered(); for (i in 1..n) out.write("$i EURUSD\n".toByteArray()); out.flush() }
    val ok = paused.await(5, TimeUnit.SECONDS)
    println("paused=$ok pauses=${pauses.get()} reads at pause=${reads.get()} peakPending=${peak.get()}")
    val r = s.getInputStream().bufferedReader()
    var got = 0
    while (got < n) { r.readLine() ?: break; got++ }
    writer.join()
    println("replies=$got reads=${reads.get()} pauses=${pauses.get()} peakPending=${peak.get()}")
    s.close(); server.close().sync(); group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
}
