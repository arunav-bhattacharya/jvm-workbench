package workbench.quotes.l01

import io.netty.buffer.ByteBuf
import io.netty.buffer.Unpooled
import io.netty.channel.ChannelFutureListener
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.embedded.EmbeddedChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import java.util.concurrent.CompletableFuture
import kotlin.text.Charsets.UTF_8

private val pendingPrices = HashMap<String, CompletableFuture<String>>()

// each request waits for a price that main() supplies by hand
private class PendingPriceHandler : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
        val (id, destination) = line.split(" ")
        val price = CompletableFuture<String>()
        pendingPrices[destination] = price
        price.whenCompleteAsync({ v, _ -> ctx.writeAndFlush("$id OK $destination $v\n") }, ctx.executor())
    }

    override fun exceptionCaught(ctx: ChannelHandlerContext, cause: Throwable) {
        ctx.writeAndFlush("ERR line too long\n").addListener(ChannelFutureListener.CLOSE)
    }
}

/** Feeds a line pipeline by hand: framing, request ids, replies out of order, and a line that is too long. */
fun main(args: Array<String>) {
    val maxLine = args.firstOrNull()?.toInt() ?: 64
    val ch = EmbeddedChannel(LineBasedFrameDecoder(maxLine), StringDecoder(UTF_8), StringEncoder(UTF_8), PendingPriceHandler())
    fun buf(s: String): ByteBuf = Unpooled.copiedBuffer(s, UTF_8)
    fun step(what: String, action: () -> Unit) {
        if (ch.isOpen) action()
        ch.runPendingTasks()                         // run the callbacks queued on the channel's loop
        val out = generateSequence { ch.readOutbound<ByteBuf>() }.map { b -> b.toString(UTF_8).trim().also { b.release() } }.toList()
        println("%-24s -> out %s".format(what, if (out.isEmpty()) "(nothing)" else out))
    }
    step("in \"7 LIS\"") { ch.writeInbound(buf("7 LIS")) }
    step("in \"BON\\n8 DUBLIN\\n\"") { ch.writeInbound(buf("BON\n8 DUBLIN\n")) }
    step("DUBLIN answers first") { pendingPrices["DUBLIN"]?.complete("9.80 fjord") }
    step("LISBON answers") { pendingPrices["LISBON"]?.complete("12.42 northline") }
    step("in a 100-byte line") { ch.writeInbound(buf("x".repeat(100) + "\n")) }
    println("channel open: ${ch.isOpen}")
}
