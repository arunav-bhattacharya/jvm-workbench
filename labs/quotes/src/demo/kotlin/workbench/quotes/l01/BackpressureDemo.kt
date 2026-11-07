package workbench.quotes.l01

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInitializer
import io.netty.channel.ChannelOption
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.SocketChannel
import io.netty.channel.socket.nio.NioServerSocketChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import io.netty.handler.flow.FlowControlHandler
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread
import kotlin.text.Charsets.UTF_8

private const val PIPELINED = 20_000
private const val IN_FLIGHT_CAP = 16
private val taken = AtomicInteger()
private val peakPending = AtomicLong()

private enum class ReadPolicy { NONE, AUTO_READ, AUTO_READ_AND_FLOW_CONTROL }

private class AnswerAtOnce(private val policy: Boolean) : SimpleChannelInboundHandler<String>() {
    private var inFlight = 0                                    // only the loop touches it

    override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
        taken.incrementAndGet()
        inFlight++
        update(ctx)
        CompletableFuture.completedFuture(line.substringBefore(' ')).whenCompleteAsync({ id, _ ->
            inFlight--
            ctx.writeAndFlush("$id OK EURUSD 1.0842 northbank\n")
            peakPending.accumulateAndGet(ctx.channel().unsafe().outboundBuffer()!!.totalPendingWriteBytes(), ::maxOf)
            update(ctx)
        }, ctx.executor())
    }

    override fun channelWritabilityChanged(ctx: ChannelHandlerContext) {
        update(ctx)
        ctx.fireChannelWritabilityChanged()
    }

    private fun update(ctx: ChannelHandlerContext) {
        if (policy) ctx.channel().config().isAutoRead = ctx.channel().isWritable && inFlight < IN_FLIGHT_CAP
    }
}

/** A client pipelines 20,000 requests and reads nothing for 500 ms. How much does the server take on? */
fun main() {
    for (mode in ReadPolicy.entries) {
        taken.set(0)
        peakPending.set(0)
        val group = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
        try {
            val server = ServerBootstrap().group(group).channel(NioServerSocketChannel::class.java)
                .childOption(ChannelOption.SO_SNDBUF, 8 * 1024)
                .childHandler(object : ChannelInitializer<SocketChannel>() {
                    override fun initChannel(ch: SocketChannel) {
                        ch.pipeline().addLast(LineBasedFrameDecoder(64), StringDecoder(UTF_8), StringEncoder(UTF_8))
                        if (mode == ReadPolicy.AUTO_READ_AND_FLOW_CONTROL) ch.pipeline().addLast(FlowControlHandler())
                        ch.pipeline().addLast(AnswerAtOnce(mode != ReadPolicy.NONE))
                    }
                })
                .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()
            val port = (server.localAddress() as InetSocketAddress).port

            Socket().use { client ->
                client.receiveBufferSize = 8 * 1024                 // a slow client with a small window
                client.connect(InetSocketAddress(InetAddress.getLoopbackAddress(), port))
                val writer = thread {
                    runCatching {
                        val out = client.getOutputStream().buffered()
                        repeat(PIPELINED) { out.write("$it EURUSD\n".toByteArray(UTF_8)) }
                        out.flush()
                    }
                }
                Thread.sleep(500)                                   // the client reads nothing for 500 ms
                val takenWhileIdle = taken.get()
                val reader = client.getInputStream().bufferedReader(UTF_8)
                var replies = 0
                while (replies < PIPELINED && reader.readLine() != null) replies++
                writer.join()
                println("%-27s taken while the client read nothing: %,6d   peak outbound: %,9d bytes   replies: %,d"
                    .format(mode, takenWhileIdle, peakPending.get(), replies))
            }
        } finally {
            group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
        }
    }
}
