package workbench.quotes.scratch

import io.netty.buffer.ByteBuf
import io.netty.buffer.Unpooled
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.embedded.EmbeddedChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import kotlinx.coroutines.*
import kotlinx.coroutines.future.future
import java.math.BigDecimal
import java.util.concurrent.CompletableFuture
import kotlin.text.Charsets.UTF_8

class H : SimpleChannelInboundHandler<String>() {
    var pending: CompletableFuture<String>? = null
    override fun channelRead0(ctx: ChannelHandlerContext, msg: String) {
        if (msg == "later") {
            val f = CompletableFuture<String>()
            pending = f
            f.whenCompleteAsync({ v, e -> ctx.writeAndFlush("async $v on ${Thread.currentThread().name}\n") }, ctx.executor())
        } else ctx.writeAndFlush("echo $msg\n")
    }
    override fun channelWritabilityChanged(ctx: ChannelHandlerContext) {
        println("writability changed: ${ctx.channel().isWritable}")
        ctx.channel().config().isAutoRead = ctx.channel().isWritable
        ctx.fireChannelWritabilityChanged()
    }
    override fun exceptionCaught(ctx: ChannelHandlerContext, cause: Throwable) {
        println("exceptionCaught: $cause")
    }
}

fun EmbeddedChannel.drain(): List<String> = buildList {
    while (true) { val b = readOutbound<ByteBuf>() ?: break; add(b.toString(UTF_8)); b.release() }
}

fun main() {
    val q = Q("EURUSD", BigDecimal("1.0842"), "fjord", false)
    println("record props: ${q.symbol} ${q.price} ${q.stale}")
    val h = H()
    val ch = EmbeddedChannel(LineBasedFrameDecoder(16), StringDecoder(UTF_8), StringEncoder(UTF_8), h)
    ch.writeInbound(Unpooled.copiedBuffer("a\nlater\n", UTF_8))
    println("after write: ${ch.drain()}")
    val t = Thread { h.pending!!.complete("X") }; t.start(); t.join()
    println("before runPendingTasks: ${ch.drain()}")
    ch.runPendingTasks()
    println("after runPendingTasks: ${ch.drain()}")
    println("inEventLoop from other thread: " + run { var r = false; val th = Thread { r = ch.eventLoop().inEventLoop() }; th.start(); th.join(); r })
    // writability
    println("autoRead=${ch.config().isAutoRead}")
    ch.unsafe().outboundBuffer()!!.setUserDefinedWritability(1, false)
    println("after udw false: writable=${ch.isWritable} autoRead=${ch.config().isAutoRead}")
    ch.unsafe().outboundBuffer()!!.setUserDefinedWritability(1, true)
    println("after udw true: writable=${ch.isWritable} autoRead=${ch.config().isAutoRead}")
    try { ch.writeInbound(Unpooled.copiedBuffer("x".repeat(40) + "\nb\n", UTF_8)) } catch (e: Exception) { println("thrown: $e") }
    println("after long line: ${ch.drain()}")
    ch.writeInbound(Unpooled.copiedBuffer("c\n", UTF_8))
    println("after c: ${ch.drain()}")
    // future cancel
    runBlocking {
        val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
        val f = scope.future { try { delay(10_000); "x" } finally { println("coroutine finally, cancelled=${!isActive}") } }
        delay(50)
        println("cancel returned ${f.cancel(true)}")
        delay(50)
        println("scope children=${scope.coroutineContext.job.children.count()}")
        val g = scope.future<String> { throw IllegalStateException("boom") }
        try { g.join() } catch (e: Exception) { println("g failed: $e ; scope active=${scope.isActive}") }
    }
}
