package workbench.nio.l03

import io.netty.buffer.ByteBuf
import io.netty.buffer.Unpooled
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInboundHandlerAdapter
import io.netty.channel.ChannelOutboundHandlerAdapter
import io.netty.channel.ChannelPromise
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.embedded.EmbeddedChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import kotlin.text.Charsets.UTF_8

/** Feeds bytes into a pipeline in fragments and prints what each stage sees, inbound and outbound. */
private fun describe(msg: Any): String {
    val text = if (msg is ByteBuf) msg.toString(UTF_8) else msg.toString()
    val type = if (msg is ByteBuf) "ByteBuf" else msg.javaClass.simpleName
    return "$type \"${text.replace("\n", "\\n")}\""
}

fun main() {
    val ch = EmbeddedChannel(
        LineBasedFrameDecoder(64),                                 // inbound: bytes -> one ByteBuf per line
        object : ChannelInboundHandlerAdapter() {                  // inbound tap
            override fun channelRead(ctx: ChannelHandlerContext, msg: Any) {
                println("   in,  after framing : ${describe(msg)}")
                ctx.fireChannelRead(msg)                           // pass it on (ownership moves with it)
            }
        },
        StringDecoder(UTF_8),                                      // inbound: ByteBuf -> String
        object : ChannelOutboundHandlerAdapter() {                 // outbound tap, nearer the head than the encoder
            override fun write(ctx: ChannelHandlerContext, msg: Any, promise: ChannelPromise) {
                println("   out, to the wire   : ${describe(msg)}")
                ctx.write(msg, promise)
            }
        },
        StringEncoder(UTF_8),                                      // outbound: String -> ByteBuf
        object : SimpleChannelInboundHandler<String>() {           // business logic, last
            override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
                println("   in,  business sees : String \"$line\"")
                ctx.writeAndFlush(line.uppercase() + "\n")         // travels toward the head
            }
        },
    )

    for (fragment in listOf("hel", "lo\nwor", "ld\n")) {
        println("writeInbound(\"${fragment.replace("\n", "\\n")}\")")
        ch.writeInbound(Unpooled.copiedBuffer(fragment, UTF_8))
        while (true) ch.readOutbound<ByteBuf>()?.release() ?: break
    }
    try {
        ch.writeInbound(Unpooled.copiedBuffer("x".repeat(100) + "\n", UTF_8))
    } catch (e: Exception) {
        println("100-byte line -> ${e.javaClass.simpleName}: ${e.message}")
    }
    println("finish() = ${ch.finish()}")
}
