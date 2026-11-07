package workbench.quotes.l01

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInitializer
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.SocketChannel
import io.netty.channel.socket.nio.NioServerSocketChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.text.Charsets.UTF_8

private val slowProvider = Executors.newSingleThreadScheduledExecutor()
private val quotesInFlight = AtomicInteger()
private val peakInFlight = AtomicInteger()

private fun slowQuote(symbol: String): CompletableFuture<String> {
    peakInFlight.accumulateAndGet(quotesInFlight.incrementAndGet(), ::maxOf)   // count quotes waiting at once
    val f = CompletableFuture<String>()
    slowProvider.schedule({ quotesInFlight.decrementAndGet(); f.complete("$symbol 1.0842") }, 100, TimeUnit.MILLISECONDS)
    return f
}

private class QuoteOnLoopKt(private val block: Boolean) : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
        val (id, symbol) = line.split(" ")
        val q = slowQuote(symbol)
        if (block) {
            ctx.writeAndFlush("$id OK ${q.join()}\n")                           // waits 100 ms on the loop
        } else {
            q.whenCompleteAsync({ v, _ -> ctx.writeAndFlush("$id OK $v\n") }, ctx.executor())
        }
    }
}

/** One event loop, ten clients, a provider that answers after 100 ms: join() on the loop vs handing the future back. */
fun main() {
    for (block in listOf(true, false)) {
        val group = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
        try {
            val server = ServerBootstrap().group(group).channel(NioServerSocketChannel::class.java)
                .childHandler(object : ChannelInitializer<SocketChannel>() {
                    override fun initChannel(ch: SocketChannel) {
                        ch.pipeline().addLast(LineBasedFrameDecoder(64), StringDecoder(UTF_8), StringEncoder(UTF_8), QuoteOnLoopKt(block))
                    }
                })
                .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()
            val port = (server.localAddress() as InetSocketAddress).port
            val clients = List(10) { Socket(InetAddress.getLoopbackAddress(), port) }

            peakInFlight.set(0)
            val t0 = System.nanoTime()
            clients.forEachIndexed { i, c -> c.getOutputStream().write("$i EURUSD\n".toByteArray(UTF_8)) }
            clients.forEach { it.getInputStream().bufferedReader(UTF_8).readLine() }
            val ms = (System.nanoTime() - t0) / 1_000_000
            println("%-6s 10 replies after %,5d ms; quotes waiting at the same time: %2d".format(if (block) "join" else "async", ms, peakInFlight.get()))
            clients.forEach { it.close() }
        } finally {
            group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
        }
    }
    slowProvider.shutdown()
}
