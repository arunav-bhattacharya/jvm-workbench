package workbench.nio.l04

import io.netty.buffer.ByteBuf
import io.netty.buffer.ByteBufUtil
import io.netty.buffer.Unpooled
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.embedded.EmbeddedChannel
import io.netty.handler.codec.ByteToMessageDecoder
import io.netty.handler.codec.LengthFieldBasedFrameDecoder
import io.netty.handler.codec.MessageToByteEncoder
import io.netty.handler.codec.TooLongFrameException
import kotlin.text.Charsets.UTF_8

/** A length-prefixed codec fed in awkward slices: [int length][byte type][UTF-8 text]. */
private data class CodecFrame(val type: Int, val text: String)

private class CodecFrameEncoder : MessageToByteEncoder<CodecFrame>() {
    override fun encode(ctx: ChannelHandlerContext, f: CodecFrame, out: ByteBuf) {
        val text = f.text.toByteArray(UTF_8)
        out.writeInt(1 + text.size).writeByte(f.type).writeBytes(text)
    }
}

private class CodecFrameDecoder : ByteToMessageDecoder() {   // runs after the length is stripped
    override fun decode(ctx: ChannelHandlerContext, input: ByteBuf, out: MutableList<Any>) {
        val type = input.readByte().toInt()
        out += CodecFrame(type, input.readCharSequence(input.readableBytes(), UTF_8).toString())
    }
}

private class CodecApprover : SimpleChannelInboundHandler<CodecFrame>() {
    override fun channelRead0(ctx: ChannelHandlerContext, f: CodecFrame) {
        ctx.writeAndFlush(CodecFrame(f.type + 1, f.text.uppercase()))
    }
}

fun main() {
    val encoder = EmbeddedChannel(CodecFrameEncoder())
    encoder.writeOutbound(CodecFrame(1, "auth-1"), CodecFrame(7, "capture-1"))
    val wire = Unpooled.buffer()
    while (true) {
        val part = encoder.readOutbound<ByteBuf>() ?: break
        wire.writeBytes(part)
        part.release()
    }
    println("wire: ${wire.readableBytes()} bytes, hex ${ByteBufUtil.hexDump(wire)}")

    val ch = EmbeddedChannel(LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4),
        CodecFrameDecoder(), CodecFrameEncoder(), CodecApprover())
    var from = 0
    for (to in listOf(3, 9, 14, wire.readableBytes())) {   // inside the length, inside body 1, across the boundary, the rest
        ch.writeInbound(wire.retainedSlice(from, to - from))
        val replies = buildList {
            while (true) {
                val out = ch.readOutbound<ByteBuf>() ?: break
                add("type=${out.getByte(4)} ${out.toString(5, out.readableBytes() - 5, UTF_8)}")
                out.release()
            }
        }
        println("bytes [%2d,%2d) -> replies %s".format(from, to, replies))
        from = to
    }
    wire.release()
    try {
        ch.writeInbound(Unpooled.buffer().writeInt(5_000).writeByte(1))
    } catch (e: TooLongFrameException) {
        println("length 5000 -> TooLongFrameException: ${e.message}")
    }
    println("finish() = ${ch.finish()}")
}
