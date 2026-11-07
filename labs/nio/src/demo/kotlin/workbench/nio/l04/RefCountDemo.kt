package workbench.nio.l04

import io.netty.buffer.ByteBufAllocator
import io.netty.buffer.Unpooled
import io.netty.util.IllegalReferenceCountException
import kotlin.text.Charsets.US_ASCII

/** A ByteBuf's two indexes and its reference count, step by step. */
fun main() {
    println("default allocator: ${ByteBufAllocator.DEFAULT.javaClass.simpleName}")
    val b = ByteBufAllocator.DEFAULT.buffer(16)
    println("buffer(16): ${b.javaClass.simpleName} direct=${b.isDirect} readerIndex=${b.readerIndex()} writerIndex=${b.writerIndex()} refCnt=${b.refCnt()}")
    b.writeInt(42).writeLong(7)
    println("after writeInt+writeLong: writerIndex=${b.writerIndex()} readableBytes=${b.readableBytes()}")
    b.readInt()
    println("after readInt: readerIndex=${b.readerIndex()} readableBytes=${b.readableBytes()} (no flip)")
    b.retain()
    println("retain(): refCnt=${b.refCnt()}")
    println("release() -> ${b.release()}, refCnt=${b.refCnt()}")
    println("release() -> ${b.release()}, refCnt=${b.refCnt()} (memory goes back to the allocator)")
    try {
        b.readLong()
    } catch (e: IllegalReferenceCountException) {
        println("readLong() after release -> ${e.javaClass.simpleName}: ${e.message}")
    }

    val header = Unpooled.copiedBuffer("HDR:", US_ASCII)
    val body = Unpooled.copiedBuffer("payload", US_ASCII)
    val frame = Unpooled.compositeBuffer()
    frame.addComponents(true, header, body)                  // no bytes copied; frame now owns both parts
    body.setByte(0, 'P'.code)
    println("composite: ${frame.toString(US_ASCII)} (sees the change to body: shared memory)")
    frame.release()
    println("composite.release(): header.refCnt=${header.refCnt()} body.refCnt=${body.refCnt()}")
}
