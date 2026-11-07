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
        val (id, symbol) = line.split(" ")
        val price = CompletableFuture<String>()
        pendingPrices[symbol] = price
        price.whenCompleteAsync({ v, _ -> ctx.writeAndFlush("$id OK $symbol $v\n") }, ctx.executor())
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
    step("in \"7 EUR\"") { ch.writeInbound(buf("7 EUR")) }
    step("in \"USD\\n8 GBPUSD\\n\"") { ch.writeInbound(buf("USD\n8 GBPUSD\n")) }
    step("GBPUSD answers first") { pendingPrices["GBPUSD"]?.complete("1.2710 fjord") }
    step("EURUSD answers") { pendingPrices["EURUSD"]?.complete("1.0842 northbank") }
    step("in a 100-byte line") { ch.writeInbound(buf("x".repeat(100) + "\n")) }
    println("channel open: ${ch.isOpen}")
}
