package workbench.nio.l03

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.Channel
import io.netty.channel.ChannelHandler
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInitializer
import io.netty.channel.EventLoopGroup
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
import java.util.concurrent.Executor
import java.util.concurrent.TimeUnit
import kotlin.text.Charsets.UTF_8

object QuotePipeline {
    const val MAX_LINE = 64

    // inbound events go head -> tail (frame, decode, business); outbound writes go tail -> head (encode)
    fun handlers(business: ChannelHandler): Array<ChannelHandler> = arrayOf(
        LineBasedFrameDecoder(MAX_LINE),
        StringDecoder(UTF_8),
        StringEncoder(UTF_8),
        business,
    )
}

class UpperCaseHandler : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, msg: String) {
        ctx.writeAndFlush(msg.uppercase() + "\n")   // goes out through StringEncoder
    }
}

class QuoteHandler(
    private val blocking: Executor,
    private val lookup: (String) -> String,
) : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
        blocking.execute {                                   // leave the event loop for the slow part
            val quote = try {
                lookup(line)
            } catch (e: Exception) {
                "error: ${e.message}"
            }
            ctx.writeAndFlush("$quote\n")                    // Netty hands the write back to the channel's event loop
        }
    }
}

class QuoteServer(blocking: Executor, lookup: (String) -> String) : AutoCloseable {
    val group: EventLoopGroup = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
    private val channel: Channel = ServerBootstrap()
        .group(group)                                        // one group: accepts and serves on the same loop
        .channel(NioServerSocketChannel::class.java)
        .childHandler(object : ChannelInitializer<SocketChannel>() {
            override fun initChannel(ch: SocketChannel) {
                ch.pipeline().addLast(*QuotePipeline.handlers(QuoteHandler(blocking, lookup)))   // new handlers per channel
            }
        })
        .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()

    fun port(): Int = (channel.localAddress() as InetSocketAddress).port

    override fun close() {
        channel.close().sync()
        group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
    }
}
