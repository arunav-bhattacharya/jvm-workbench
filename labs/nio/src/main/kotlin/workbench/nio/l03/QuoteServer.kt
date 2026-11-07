package workbench.nio.l03

import io.netty.channel.Channel
import io.netty.channel.ChannelHandler
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.EventLoopGroup
import io.netty.channel.SimpleChannelInboundHandler
import java.net.InetSocketAddress
import java.util.concurrent.Executor
import java.util.concurrent.TimeUnit

/** The pipeline of a line-based quote server. */
object QuotePipeline {
    const val MAX_LINE = 64

    /**
     * The handlers, in pipeline order:
     * 1. `LineBasedFrameDecoder(MAX_LINE)`: bytes in, one `ByteBuf` per line out (no `\n`)
     * 2. `StringDecoder(UTF_8)`: `ByteBuf` in, `String` out
     * 3. `StringEncoder(UTF_8)`: outbound `String` in, `ByteBuf` out
     * 4. [business]: your handler, last
     */
    fun handlers(business: ChannelHandler): Array<ChannelHandler> =
        TODO("return the four handlers in order")
}

/** Replies to each line with the line in upper case, followed by `\n`. */
class UpperCaseHandler : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, msg: String) {
        TODO("write msg.uppercase() + \"\\n\" and flush")
    }
}

/**
 * Answers each line with `lookup(line)`. The lookup may block (it stands in for a JDBC call),
 * and this version calls it on the event loop. Fix it: run the lookup on [blocking] and write the
 * reply from there. `ctx.writeAndFlush` is safe to call from any thread.
 */
class QuoteHandler(
    private val blocking: Executor,
    private val lookup: (String) -> String,
) : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
        val quote = lookup(line)            // BUG: a slow lookup stalls every channel on this event loop
        ctx.writeAndFlush("$quote\n")
    }
}

/**
 * A TCP quote server on 127.0.0.1 and a free port, with ONE event loop thread.
 *
 * Build it with the Netty 4.2 API:
 * - [group]: `MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())`
 * - a `ServerBootstrap` with `.group(group)`, `.channel(NioServerSocketChannel::class.java)` and a
 *   `childHandler` (`ChannelInitializer<SocketChannel>`) that adds
 *   `QuotePipeline.handlers(QuoteHandler(blocking, lookup))` to each new channel's pipeline
 * - `.bind(InetAddress.getLoopbackAddress(), 0).sync().channel()`
 */
class QuoteServer(blocking: Executor, lookup: (String) -> String) : AutoCloseable {
    val group: EventLoopGroup = TODO("one event loop thread, NIO transport")
    private val channel: Channel = TODO("bootstrap, bind and return the server channel")

    fun port(): Int = (channel.localAddress() as InetSocketAddress).port

    override fun close() {
        channel.close().sync()
        group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
    }
}
